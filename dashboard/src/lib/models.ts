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
	source: string;
	sink: string;
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
	ip: string;
	name: string;
	id: string;
	port: number;
	running: boolean;
	data_type: 'Video' | 'Series' | 'Audio';
	dashboard_component: null | string;
}

export interface Worker {
	ip: string;
	name: string;
	id: string;
	port: number;
	nodes: Node[];
}

export interface Graph {
	id: string;
}

export interface Manager {
	ip: string; // Define proper IP
	status: ManagerStatus;
	port: number;
	workers: Worker[];
	graph?: Graph;
	worker_graph_map?: { string: string }[];
	network_updates_port: number;
}
