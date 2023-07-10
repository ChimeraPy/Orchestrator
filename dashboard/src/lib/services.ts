import { dev } from '$app/environment';
import { PipelineClient, ClusterClient } from './Services/Client';

const URL = dev ? '/api' : '';

export const clusterClient = new ClusterClient(URL);
export const pipelineClient = new PipelineClient(URL);
