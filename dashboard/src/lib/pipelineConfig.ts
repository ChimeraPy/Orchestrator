/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * The pipeline_service config.
 */
export interface ChimeraPyPipelineConfig {
	/**
	 * The mode of the pipeline_service.
	 */
	mode?: 'preview' | 'record';
	/**
	 * The name of the pipeline
	 */
	name?: string;
	/**
	 * The description of the pipeline.
	 */
	description?: string;
	/**
	 * The workers to be added.
	 */
	workers: Workers;
	/**
	 * The nodes in the pipeline_service.
	 */
	nodes: NodeConfig[];
	/**
	 * The edge list of the pipeline_service graph.
	 */
	adj: [string, string][];
	/**
	 * The manager configs.
	 */
	manager_config: ManagerConfig;
	/**
	 * The delegation mapping of workers to nodes.
	 */
	mappings: {
		[k: string]: string[];
	};
	/**
	 * The list of modules to discover nodes from. Deprecated. see NodeConfig.package.
	 */
	discover_nodes_from?: string[];
	/**
	 * The timeouts for the pipeline operation.
	 */
	timeouts?: Timeouts;
}
/**
 * A list of workers.
 */
export interface Workers {
	/**
	 * The manager ip.
	 */
	manager_ip: string;
	/**
	 * The manager port.
	 */
	manager_port: number;
	/**
	 * The workers to be added.
	 */
	instances: WorkerConfig[];
}
export interface WorkerConfig {
	/**
	 * The name of the worker.
	 */
	name: string;
	/**
	 * The id of the worker.
	 */
	id?: string;
	/**
	 * Indicating the worker is remote and is connected(no creation needed).
	 */
	remote?: boolean;
	/**
	 * The description of the worker.
	 */
	description?: string;
}
export interface NodeConfig {
	/**
	 * The name of the node to search in the registry.
	 */
	registry_name: string;
	/**
	 * The name of the node.
	 */
	name: string;
	/**
	 * The kwargs for the node.
	 */
	kwargs?: {
		[k: string]: unknown;
	};
	/**
	 * The package that registered this node.
	 */
	package?: string;
}
export interface ManagerConfig {
	/**
	 * The log directory for the manager.
	 */
	logdir: string;
	/**
	 * The port for the manager.
	 */
	port: number;
}
export interface Timeouts {
	/**
	 * The timeout for the commit operation in seconds.
	 */
	commit_timeout?: number;
	/**
	 * The timeout for the preview operation in seconds.
	 */
	preview_timeout?: number;
	/**
	 * The timeout for the record operation in seconds.
	 */
	record_timeout?: number;
	/**
	 * The timeout for the commit operation in seconds.
	 */
	collect_timeout?: number;
	/**
	 * The timeout for the stop operation in seconds.
	 */
	stop_timeout?: number;
	/**
	 * The timeout for shutdown operation in seconds.
	 */
	shutdown_timeout?: number;
}
