import { describe, it, expect } from 'vitest';

import type { NodeState, WorkerState } from '../../lib/models';
import { networkEntityDetails } from '../../lib/utils';

describe('utils', () => {
	it('should return proper object description for a node', () => {
		const node: NodeState = {
			id: 'Some Random Id',
			port: 8001,
			name: 'My Node',
			ready: true,
			finished: false,
			connected: true,
			init: true
		};

		const detailsString = networkEntityDetails(node, 0, 'Node');

		expect(detailsString).toBe(`Node #1 name = ${node.name} @ ${node.port}`); // Follow Jest
	});

	it('should return proper object description for a worker', () => {
		const worker: WorkerState = {
			id: 'Some Random Id',
			ip: 'http://localhost',
			port: 8001,
			name: 'My Worker',
			nodes: []
		};
		const detailsString = networkEntityDetails(worker, 0, 'Worker');

		expect(detailsString).toBe(`Worker #1 name = ${worker.name} @ ${worker.ip}:${worker.port}`); // Follow Jest
	});
});
