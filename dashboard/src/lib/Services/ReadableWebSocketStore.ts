import { writable } from 'svelte/store';
import type { Readable, Subscriber } from 'svelte/store';

const reopenTimeouts = [2000, 5000, 10000, 30000, 60000];

export default function readableWebSocketStore<T>(
	path: string,
	initialValue: T|null,
	mapper: (data: any) => T,
	origin: string|null = null
): Readable<T|null> {
	const { subscribe, update } = writable<T|null>(initialValue);
	const subscribers = new Set<Subscriber<T>>();

	const socket = new WebSocket(`ws://${origin || window.location.host}${path}`);
	socket.onopen = () => {
		console.log('WebSocket opened');
	}

	socket.onmessage = (event) => {
		const data = JSON.parse(event.data);
		console.log(data)
		update((value) => {
			const newValue = mapper(data);
			if (newValue !== value) {
				return newValue;
			}
			return value;
		});
	};

	return {
		'subscribe': (subscriber) => {
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
