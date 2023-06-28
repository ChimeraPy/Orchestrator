import * as joint from 'jointjs';
import * as graphlib from 'graphlib';

export type ValidatorFunc = (linkView: joint.dia.LinkView, paper: joint.dia.Paper) => boolean;
export type DispatcherFunc = (cell: joint.dia.Cell) => void;

export type ToolOptions =
	| joint.elementTools.Button.Options
	| joint.elementTools.HoverConnect.Options;
export enum ToolViewType {
	HOVER_CONNECT = 'hoverconnect',
	INFO = 'info',
	DELETE = 'remove'
}

export class LinkValidator {
	private validators: ValidatorFunc[];

	constructor(validators: ValidatorFunc[] = []) {
		this.validators = [nonNullValidator, isAcyclic, isNotLinkToSelf];
		if (validators.length > 0) {
			this.validators = [...this.validators, ...validators];
		}
	}

	isValidLink(linkView: joint.dia.LinkView, paper: joint.dia.Paper): boolean {
		return this.validators.every((validator) => validator(linkView, paper));
	}
}

const isAcyclic = (linkView: joint.dia.LinkView, paper: joint.dia.Paper) => {
	const graph = paper.model;
	return graphlib.alg.isAcyclic(
		graph.toGraphLib({
			directed: true,
			multigraph: true,
			compound: true,
			dagre: true,
			graphlib: graphlib
		})
	);
};

const nonNull = <T>(x: T | null): x is T => x !== null;

const isNotLinkToSelf = (linkView: joint.dia.LinkView, paper: joint.dia.Paper) => {
	const link = linkView.model;
	const src = link.getSourceElement();
	const tgt = link.getTargetElement();
	return src.id !== tgt.id;
};

const nonNullValidator = (linkView: joint.dia.LinkView, paper: joint.dia.Paper) => {
	const link = linkView.model;
	const src = link.getSourceElement();
	const tgt = link.getTargetElement();
	return nonNull<joint.dia.Cell>(src) && nonNull<joint.dia.Cell>(tgt);
};

export function getToolType(
	type: ToolViewType,
	dipatcher: DispatcherFunc | null,
	options?: ToolOptions
): joint.elementTools.Button | joint.elementTools.HoverConnect {
	let tool;
	switch (type) {
		case ToolViewType.HOVER_CONNECT:
			tool = getConnectTool(dipatcher, options as joint.elementTools.HoverConnect.Options);
			break;
		case ToolViewType.INFO:
			tool = getInfoTool(dipatcher, options as joint.elementTools.Button.Options);
			break;
		case ToolViewType.DELETE:
			tool = getDeleteTool(dipatcher, options as joint.elementTools.Button.Options);
			break;
		default:
			throw new Error(`Tool type ${type} not supported`);
	}

	return tool;
}

const defaultsDeep = <T extends object>(source: T, destination: T): T => {
	return joint.util.defaultsDeep(source, destination) as T;
};

export const getConnectTool = (
	dispatcher: DispatcherFunc | null,
	options: joint.elementTools.HoverConnect.Options
) => {
	options = defaultsDeep<joint.elementTools.HoverConnect.Options>(options || {}, {
		magnet: 'body',
		markup: [
			{
				tagName: 'circle',
				selector: 'body',
				attributes: {
					r: 7,
					fill: 'gray',
					stroke: 'black',
					'stroke-width': 1,
					cursor: 'pointer'
				}
			}
		]
	});

	if (dispatcher) {
		options.action = function (evt) {
			dispatcher(this.model);
		};
	}

	return new joint.elementTools.HoverConnect(options);
};

export const getInfoTool = (
	dispatcher: DispatcherFunc | null,
	options: joint.elementTools.HoverConnect.Options
) => {
	options = defaultsDeep<joint.elementTools.HoverConnect.Options>(options || {}, {
		focusOpacity: 0.5,
		// top-right corner
		x: '100%',
		y: '0%',
		markup: [
			{
				tagName: 'circle',
				selector: 'button',
				attributes: {
					r: 7,
					fill: '#001DFF',
					cursor: 'pointer'
				}
			},
			{
				tagName: 'path',
				selector: 'icon',
				attributes: {
					d: 'M -2 4 2 4 M 0 3 0 0 M -2 -1 1 -1 M -1 -4 1 -4',
					fill: 'none',
					stroke: '#FFFFFF',
					'stroke-width': 2,
					'pointer-events': 'none'
				}
			}
		]
	});

	if (dispatcher) {
		options.action = function (evt) {
			dispatcher(this.model);
		};
	}

	const infoBtn = new joint.elementTools.Button(options);

	return infoBtn;
};

export const getAddTool = (
	dispatcher: DispatcherFunc | null,
	options: joint.elementTools.HoverConnect.Options
) => {
	options = defaultsDeep<joint.elementTools.HoverConnect.Options>(options || {}, {
		focusOpacity: 0.5,
		// top-right corner
		x: '100%',
		y: '0%',
		markup: [
			{
				tagName: 'circle',
				selector: 'button',
				attributes: {
					r: 10,
					fill: '#EC007C',
					cursor: 'pointer'
				}
			},
			{
				tagName: 'path',
				selector: 'icon',
				attributes: {
					d: 'M0,-5 V5 M-5,0 H5',
					fill: 'none',
					stroke: '#000000',
					'stroke-width': 2,
					'pointer-events': 'none'
				}
			}
		]
	});

	if (dispatcher) {
		options.action = function (evt) {
			dispatcher(this.model);
		};
	}

	const addBtn = new joint.elementTools.Button(options);

	return addBtn;
};

export const getDeleteTool = (
	dispatcher: DispatcherFunc | null,
	options: joint.elementTools.HoverConnect.Options
) => {
	options = defaultsDeep<joint.elementTools.HoverConnect.Options>(options || {}, {
		offset: {
			x: -10,
			y: -10
		}
	});

	if (dispatcher) {
		options.action = function (evt) {
			dispatcher(this.model);
		};
	}

	return new joint.elementTools.Remove(options);
};
