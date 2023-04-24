import { writable } from 'svelte/store';
import type { Readable, Subscriber } from 'svelte/store';

const reopenTimeouts = [2000, 5000, 10000, 30000, 60000];

export default function readableWebSocketStore<T>(
	path: string,
	initialValue: T | null,
	mapper: (data: any) => T,
	origin: string | null = null
): Readable<T | null> {
	const { subscribe, update } = writable<T | null>(initialValue);
	const subscribers = new Set<Subscriber<T>>();
	let reopenCount = 0;
	let openPromise: Promise<void> | null = null;
	let reopenTimeoutHandler: ReturnType<typeof setTimeout> | null = null;
	let socket: WebSocket | null = null;

	function reopenTimeout() {
		const n = reopenCount;
		reopenCount++;
		return reopenTimeouts[n >= reopenTimeouts.length - 1 ? reopenTimeouts.length - 1 : n];
	}

	const open = () => {
		if (reopenTimeoutHandler) {
			clearTimeout(reopenTimeoutHandler);
			reopenTimeoutHandler = null;
		}
		if (openPromise) {
			return openPromise;
		}

		socket = new WebSocket(`ws://${origin || window.location.host}${path}`);
		socket.onmessage = (event) => {
			const data = JSON.parse(event.data);
			update((value) => {
				const newValue = mapper(data);
				if (newValue !== value) {
					return newValue;
				}
				return value;
			});
		};

		socket.onclose = (event) => {
			reopen();
		};

		openPromise = new Promise((resolve, reject) => {
			if (socket) {
				socket.onerror = (event) => {
					update(() => null);
					reject(event);
					openPromise = null;
				};

				socket.onopen = (event) => {
					reopenCount = 0;
					resolve();
					openPromise = null;
				};
			}
		});

		return openPromise;
	};

	const reopen = () => {
		close();
		if (subscribers.size > 0) {
			reopenTimeoutHandler = setTimeout(() => open(), reopenTimeout());
		}
	};

	const close = () => {
		if (socket) {
			socket.close();
			socket = null;
		}
	};

	return {
		subscribe: (subscriber) => {
			open();
			subscribers.add(subscriber);
			subscribe(subscriber);
			return () => {
				subscribers.delete(subscriber);
				if (subscribers.size === 0) {
					close();
				}
			};
		}
	};
}
