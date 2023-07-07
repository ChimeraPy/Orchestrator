import type { Result } from 'ts-monads/lib/Result';
import type {
	PipelineNode,
	Pipeline,
	Edge,
	ResponseError,
	ClusterState,
	ActionsFSM,
	NodesPlugin
} from '../models';
import { Err, Ok } from 'ts-monads';
import type { ChimeraPyPipelineConfig } from '$lib/pipelineConfig';

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
			if (res.status < 500) {
				return new Err({
					message: res.statusText,
					code: res.status,
					serverMessage: await res.json()
				});
			} else {
				return new Err({
					message: res.statusText,
					code: res.status,
					serverMessage: await res.text()
				});
			}
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

	async importPipeline(config: ChimeraPyPipelineConfig): Promise<Result<Pipeline, ResponseError>> {
		const prefix = '/create';

		const requestBody = {
			config: config
		};

		const response = await this._fetch<Pipeline>(prefix, {
			method: 'PUT',
			body: JSON.stringify(requestBody),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async getPlugins(): Promise<Result<NodesPlugin[], ResponseError>> {
		const prefix = '/plugins';
		const response = await this._fetch<NodesPlugin[]>(prefix, { method: 'GET' });

		return response;
	}

	async installPlugin(pluginName: string): Promise<Result<PipelineNode[], ResponseError>> {
		const prefix = encodeURIComponent(`/install-plugin/${pluginName}`);
		const response = await this._fetch<PipelineNode[]>(prefix, { method: 'POST' });

		return response;
	}

	async updatePipeline(
		pipelineId: string,
		pipeline: Pipeline
	): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/update/${pipelineId}`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'POST',
			body: JSON.stringify(pipeline),
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}
}

export class ClusterClient extends Client {
	constructor(serverURL: string, prefix: string = '/cluster') {
		super(serverURL + prefix);
	}

	async enableZeroConf(): Promise<Result<boolean, ResponseError>> {
		const prefix = '/zeroconf?enable=true';
		const result = await this._fetch<any>(prefix, { method: 'POST' });
		return result.map((_) => true);
	}

	async disableZeroConf(): Promise<Result<boolean, ResponseError>> {
		const prefix = '/zeroconf?enable=false';
		const result = await this._fetch<any>(prefix, { method: 'POST' });
		return result.map((_) => true);
	}

	async instantiatePipeline(pipelineID: string): Promise<Result<boolean, ResponseError>> {
		const prefix = `/instantiate/${pipelineID}`;
		const result = await this._fetch<boolean>(prefix, { method: 'POST' });
		return result.map((_) => true);
	}

	async commitPipeline(): Promise<Result<boolean, ResponseError>> {
		const prefix = `/commit`;
		const result = await this._fetch<boolean>(prefix, { method: 'POST' });
		return result.map((_) => true);
	}

	async getActionsFSM(): Promise<Result<ActionsFSM, ResponseError>> {
		const prefix = '/actions-fsm';
		const response = await this._fetch<ActionsFSM>(prefix, { method: 'GET' });

		return response;
	}
}
