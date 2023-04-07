import { Ok, Err } from 'ts-monads';
import type { Result } from 'ts-monads/lib/Result';
import type { PipelineNode, Pipeline } from '../models';
import type { ResponseError } from './NetworkApi';

export class PipelineApi {
	url: string;

	constructor(serverURL: string, prefix: string = '/pipeline') {
		this.url = serverURL + prefix;
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

	async deletePipeline(id: string): Promise<Result<Pipeline, ResponseError>> {
		const prefix = encodeURIComponent(`/delete/${id}`);
		const response = await this._fetch<Pipeline>(prefix, {
			method: 'DELETE',
			headers: new Headers({ 'Content-Type': 'application/json' })
		});

		return response;
	}

	async addEdgeTo(
		pipeline_id: string,
		src: PipelineNode,
		tgt: PipelineNode
	): Promise<Result<PipelineNode, ResponseError>> {
		const prefix = encodeURIComponent(`/add-edge/${pipeline_id}`);

		const requestBody = {
			source: src,
			target: tgt
		};

		const response = await this._fetch<PipelineNode>(prefix, {
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
			method: 'DELETE',
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

	async _fetch<T>(prefix: string, options: RequestInit): Promise<Result<T, ResponseError>> {
		const res = await fetch(this.url + prefix, options);
		if (res.ok) {
			return new Ok<T>(await res.json());
		} else {
			return new Err({ message: res.statusText, code: res.status });
		}
	}
}
