import { dev } from '$app/environment';
import { NetworkClient, PipelineClient } from './Services/Client';

const URL = dev ? '/api' : '';

export const networkClient = new NetworkClient(URL);
export const pipelineClient = new PipelineClient(URL);
