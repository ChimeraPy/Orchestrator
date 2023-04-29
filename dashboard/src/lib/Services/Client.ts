import type { Result } from 'ts-monads/lib/Result';
import type { PipelineNode, Pipeline, Edge, ResponseError, ClusterState, ActionsFSM } from '../models';
import { Err, Ok } from 'ts-monads';

class Client {
	url: string;

	protected constructor(url: string) {
		this.url = url;
	}

	async _fetch<T>(prefix: string, options: RequestInit): Promise<Result<T, ResponseError>> {
		const res = await fetch(this.url + prefix, options);
		if (res.ok) {
			return new Ok<T>(await res.json());
		} else {
			return new Err({ message: res.statusText, code: res.status, body: await res.json() });
		}
	}
}

export class PipelineClient extends Client {
	constructor(serverURL: string, prefix: string = '/pipeline') {
		super(serverURL + prefix);
	}

	async getNodes(): Promise<Result<PipelineNode[], ResponseError>> {
		const prefix = '/list-nodes';
		const response = await this._fetch<PipelineNode[]>(prefix, { method: 'GET' });

		return response;
	}

	async getPipelines(): Promise<Result<Pipeline[], ResponseError>> {
		const prefix = '/list';
		const response = await this._fetch<Pipeline[]>(prefix, { method: 'GET' });

		return response;
	}

	async getPipeline(id: string): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/get/${id}`);
		const response = await this._fetch<Pipeline>(prefix, { method: 'GET' });
		return response;
	}

	async removePipeline(id: string): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/remove/${id}`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'DELETE',
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async addEdgeTo(
		pipeline_id: string,
		src: PipelineNode,
		sink: PipelineNode,
		edgeId: string
	): Promise<Result<Edge, ResponseError>> {
		const prefix = encodeURIComponent(`/add-edge/${pipeline_id}`);

		const requestBody = {
			source: src,
			sink: sink,
			id: edgeId
		};

		const response = await this._fetch<Edge>(prefix, {
			method: 'POST',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async removeEdgeFrom(
		pipeline_id: string,
		src: PipelineNode,
		sink: PipelineNode,
		edgeId: string
	): Promise<Result<Edge, ResponseError>> {
		const prefix = encodeURIComponent(`/remove-edge/${pipeline_id}`);
		const requestBody = {
			source: src,
			sink: sink,
			id: edgeId
		};

		const response = await this._fetch<Edge>(prefix, {
			method: 'POST',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async addNodeTo(
		pipelineId: string,
		node: PipelineNode
	): Promise<Result<PipelineNode, ResponseError>> {
		const prefix = encodeURIComponent(`/add-node/${pipelineId}`);

		const requestBody = node;

		const response = await this._fetch<PipelineNode>(prefix, {
			method: 'POST',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async removeNodeFrom(
		pipelineId: string,
		node: PipelineNode
	): Promise<Result<PipelineNode, ResponseError>> {
		const prefix = encodeURIComponent(`/remove-node/${pipelineId}`);
		const requestBody = node;

		const response = await this._fetch<PipelineNode>(prefix, {
			method: 'POST',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async createPipeline(
		name: string,
		description = 'A pipeline'
	): Promise<Result<Pipeline, ResponseError>> {
		const prefix = '/create';

		const requestBody = {
			name: name,
			description: description
		};
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'PUT',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}
}

export class ClusterClient extends Client {
	constructor(serverURL: string, prefix: string = '/cluster') {
		super(serverURL + prefix);
	}

	async getClusterState(): Promise<Result<ClusterState, ResponseError>> {
		const prefix = '/state';
		const response = await this._fetch<ClusterState>(prefix, { method: 'GET' });

		return response;
	}

	async commitPipeline(): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/commit`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
		});

		return response;
	}

	async previewPipeline(): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/preview`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
		});

		return response;
	}

	async recordPipeline(): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/record`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
		});

		return response;
	}

	async stopPipeline(): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/stop`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
		});

		return response;
	}

	async resetPipeline(): Promise<Result<PipelineNode, ResponseError>> {
		const prefix = encodeURIComponent(`/reset`);
		const response = await this._fetch<PipelineNode>(prefix, {
			method: 'POST',
		});

		return response;
	}

	async assignWorkers(pipeline: Pipeline): Promise<Result<PipelineNode, ResponseError>> {
		const nodes = pipeline.nodes;

		const prefix = encodeURIComponent(`/assign-workers/${pipeline.id}`);
		const response = await this._fetch<PipelineNode>(prefix, {
			method: 'POST',
			body: JSON.stringify(nodes),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async activatePipeline(pipelineId: string): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/activate-pipeline/${pipelineId}`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async getActionsFSM(): Promise<Result<ActionsFSM, ResponseError>> {
		const prefix = '/actions-fsm';
		const response = await this._fetch<ActionsFSM>(prefix, { method: 'GET' });

		return response;
	}


}

export class NetworkClient extends Client {
	constructor(url: string) {
		super(url);
	}

	async getNetworkMap(
		fetch: (input: RequestInfo | URL, init?: RequestInit | undefined) => Promise<Response>
	): Promise<Ok<ClusterState> | Err<ResponseError>> {
		const res = await fetch('/mocks/networkMap.json');
		if (res.ok) {
			return new Ok(await res.json());
		} else {
			return new Err({ message: res.statusText, code: res.status,  });
		}
	}

	async load(
		fetch: (input: RequestInfo | URL, init?: RequestInit | undefined) => Promise<Response>
	) {
		console.log(await (await fetch(`${this.url}/network`)).json());
	}

	async subscribeToLogsZMQ(ip: string, port: number, callable: (e: MessageEvent) => void) {
		const ws = new WebSocket(`ws://localhost:${port}/logs`);
		ws.onmessage = (e) => {
			callable(e);
		};

		ws.onerror = (e) => {
			console.error(e);
		};

		const close = () => {
			ws.close();
		};

		return close;
	}

	async createPipeline() {}

	async deletePipeline() {}
}
