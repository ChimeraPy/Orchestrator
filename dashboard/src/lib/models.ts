// ToDo: A lot of interface modeling needs to happen here.

export enum ManagerStatus {
	STARTED = 'STARTED',
	RUNNING = 'RUNNING',
	WORKERS_READY = 'WORKERS_READY',
	PIPELINE_READY = 'PIPELINE_READY',
	PAUSED = 'PAUSED',
	STOPPED = 'STOPPED'
}

export enum NodeType {
	SOURCE = 'SOURCE',
	STEP = 'STEP',
	SINK = 'SINK'
}

export interface Dimension {
	width: number;
	height: number;
}

export enum CreatePipelineStages {
	OK = 'OK',
	ERROR = 'ERROR',
	CREATING = 'CREATING',
	ACTIVE = 'ACTIVE',
	INACTIVE = 'INACTIVE'
}

export interface PipelineNode {
	id: string;
	name: string;
	registry_name: string;
	type: NodeType;
	kwargs: { [key: string]: any };
}

export interface Edge {
	id: string;
	source: PipelineNode;
	sink: PipelineNode;
}

export interface Pipeline {
	id: string;
	name: string;
	description: string;
	instantiated: boolean;
	nodes: PipelineNode[];
	edges: Edge[];
}

export interface Node {
	id: string;
	name: string;
	port: number;
	init: boolean;
	connected: boolean;
	ready: boolean;
	finished: boolean;
}

export interface WorkerState {
	ip: string;
	name: string;
	id: string;
	port: number;
	nodes: {[key: string]: Node}[];
}

export interface ClusterState {
	id: string; // Define proper IP
	ip: string;
	port: number;
	workers: {[key: string]: Worker}[];
	logs_subscription_port?: number,
	collection_status?: string;
	running: boolean;
	collecting: boolean;
}

export interface ResponseError {
	message: string;
	code: number;
}
