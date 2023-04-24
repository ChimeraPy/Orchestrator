import { dev } from '$app/environment';
import { NetworkClient, PipelineClient, ClusterClient } from './Services/Client';

const URL = dev ? '/api' : '';

export const networkClient = new NetworkClient(URL);
export const pipelineClient = new PipelineClient(URL);
export const clusterClient = new ClusterClient(URL);
