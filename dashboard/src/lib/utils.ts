import type { WorkerState, NodeState } from './models';

export function networkEntityDetails(
	entity: WorkerState | NodeState,
	index: number,
	prefix = 'Worker'
): string {
	const details = [
		prefix,
		`#${index + 1}`,
		'name =',
		entity.name,
		'@',
		entity.ip ? `${entity.ip}:${entity.port}` : `${entity.port}`
	];
	return details.join(' ');
}

export function awaitableDelay(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

export const debounce = (fn: Function, ms = 300) => {
	let timeoutId: ReturnType<typeof setTimeout>;
	return function (this: any, ...args: any[]) {
		clearTimeout(timeoutId);
		timeoutId = setTimeout(() => fn.apply(this, args), ms);
	};
};
