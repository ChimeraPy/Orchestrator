// ToDo: A lot of interface modeling needs to happen here.
import type { NodeAttributeMeta } from './NodeAttributes';

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
	package: string;
	attributes_meta: { [key: string]: NodeAttributeMeta };
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
	committed: boolean;
	nodes: PipelineNode[];
	edges: Edge[];
}

export interface NodeState {
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
	nodes: { [key: string]: NodeState }[];
}

export interface ClusterState {
	id: string; // Define proper IP
	ip: string;
	port: number;
	workers: { [key: string]: WorkerState };
	logs_subscription_port?: number;
	collection_status?: string;
	running: boolean;
	collecting: boolean;
	zeroconf_discovery: boolean;
}

export interface ResponseError {
	message: string;
	code: number;
}

export interface NodesPlugin {
	package: string;
	nodes: string[];
	version: string;
	name: string;
	description: string;
}

export interface SelectedPipeline {
	pipeline: Pipeline | null;
	selectedNodeId: string | null;
}

export interface Transition {
	name: string;
	from_state: string;
	to_state: string;
}

export interface ActionsFSMState {
	name: string;
	description: string;
	valid_transitions: Transition[];
}

export interface ActionsFSM {
	current_state: string;
	states: { [key: string]: ActionsFSMState }[];
	description: string;
	active_pipeline_id: string | null;
}

export interface LifeCycle {
	fsm: ActionsFSM;
	pipeline: Pipeline;
}
