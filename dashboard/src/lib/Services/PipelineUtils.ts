import * as joint from 'jointjs';
import type { Result } from 'ts-monads/lib/Result';
import type { PipelineNode, Pipeline, ResponseError } from '../models';
import { NodeType } from '../models';

export class PipelineUtils {
	static validLinkTypes = [
		{
			src: NodeType.SOURCE,
			tgt: NodeType.STEP
		},
		{
			src: NodeType.STEP,
			tgt: NodeType.SINK
		},
		{
			src: NodeType.SOURCE,
			tgt: NodeType.SINK
		}
	];

	static rectangle(
		text: string,
		color: string = 'gray',
		id: string = ''
	): joint.shapes.standard.Rectangle {
		return new joint.shapes.standard.Rectangle({
			id: id || joint.util.uuid(),
			size: { width: 200, height: 50 }, // ToDo: make this dynamic
			attrs: {
				body: {
					fill: color,
					stroke: 'black',
					strokeWidth: 1,
					rx: 5,
					ry: 5
				},
				label: {
					text: text,
					fill: 'white'
				}
			}
		});
	}

	static pipelineResultToJointCells(result: Result<Pipeline, ResponseError>): joint.dia.Cell[] {
		let cells: joint.dia.Cell[] = [];

		result
			.map((pipeline) => {
				pipeline.nodes.forEach((node) => {
					const rect = PipelineUtils.rectangle(node.name, 'green', node.id);
					rect.prop('nodeId', node.id);
					rect.prop('nodeType', node.type);
					rect.prop('registryName', node.registry_name);
					cells.push(rect);
				});
				pipeline.edges.forEach((edge) => {
					const link = new joint.shapes.standard.Link({
						id: edge.id,
						source: { id: edge.source },
						target: { id: edge.sink }
					});
					cells.push(link);
				});
			})
			.mapError((error) => {
				cells.push(PipelineUtils.rectangle(error.message, 'red'));
			});

		return cells;
	}

	static pipelineNodeResultToJointCells(
		result: Result<PipelineNode[], ResponseError>
	): joint.dia.Cell[] {
		let cells: joint.dia.Cell[] = [];
		result.map((nodes) => {
			return nodes
				.sort((node1, node2) => {
					if (node1.name < node2.name) {
						return -1;
					} else if (node1.name > node2.name) {
						return 1;
					} else {
						return 0;
					}
				})
				.map((node) => {
					const rect = PipelineUtils.rectangle(node.name);
					rect.prop('nodeId', node.id);
					rect.prop('nodeType', node.type);
					rect.prop('registryName', node.registry_name);
					cells.push(rect);
				});
		});
		return cells;
	}

	static committablePipelineToJointCells(pipeline: Pipeline): joint.dia.Cell[] {
		const getNodeColor = (node: PipelineNode): string => {
			if (node.committed) return 'green';
			if (node.instance_id) return 'yellow';
			return 'gray';
		};

		const getTextColor = (node: PipelineNode): string => {
			if (node.instance_id) return 'black';
			return 'white';
		};

		return pipeline.nodes
			.map((node) => {
				const rect = PipelineUtils.rectangle(node.name, getNodeColor(node), node.id);
				rect.prop('nodeId', node.id);
				rect.prop('instanceId', node.instance_id);
				rect.prop('workerId', node.worker_id);
				rect.prop('nodeType', node.type);
				rect.prop('registryName', node.registry_name);
				rect.attr('label/fill', getTextColor(node));
				return rect as joint.dia.Cell;
			})
			.concat(
				pipeline.edges.map((edge) => {
					const link = new joint.shapes.standard.Link({
						id: edge.id,
						source: { id: edge.source },
						target: { id: edge.sink }
					});
					return link as joint.dia.Cell;
				})
			);
	}

	static pipelinesResultToEditableListItems(
		result: Result<Pipeline[], ResponseError>,
		activePipeline: Pipeline | null | undefined
	): { id: string; text: string; active: boolean }[] {
		let items: { id: string; text: string; active: boolean }[] = [];
		result.map((pipelines) => {
			return pipelines.reverse().map((pipeline, index) => {
				items.push({
					id: pipeline.id,
					text: pipeline.name,
					active: activePipeline ? activePipeline.id === pipeline.id : index === 0
				});
			});
		});

		return items;
	}

	static isValidLink(linkView: joint.dia.LinkView, paper: joint.dia.Paper): boolean {
		const link = linkView.model;
		const src = link.getSourceElement().prop('nodeType');
		const tgt = link.getTargetElement().prop('nodeType');
		return PipelineUtils.validLinkTypes.some((type) => type.src === src && type.tgt === tgt);
	}
}
