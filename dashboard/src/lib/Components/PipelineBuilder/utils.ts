import * as joint from 'jointjs';
import * as graphlib from 'graphlib';

export type ValidatorFunc = (linkView: joint.dia.LinkView, paper: joint.dia.Paper) => boolean;

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

export const getConnectTool = () => {
	return new joint.elementTools.HoverConnect({
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
};

export const getInfoButton = (dispatcher: (cell: joint.dia.Cell) => void) => {
	const infoBtn = new joint.elementTools.Button({
		focusOpacity: 0.5,
		// top-right corner
		x: '100%',
		y: '0%',
		action: function (evt) {
			dispatcher(this.model);
		},
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

	return infoBtn;
};

export const getAddButton = (dispatcher: (cell: joint.dia.Cell) => void) => {
	const addBtn = new joint.elementTools.Button({
		focusOpacity: 0.5,
		// top-right corner
		x: '100%',
		y: '0%',
		action: function (evt) {
			dispatcher(this.model);
		},
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

	return addBtn;
};

export const getDeleteButton = (dispatcher: (cell: joint.dia.Cell) => void) => {
	return new joint.elementTools.Remove({
		action: function (evt) {
			dispatcher(this.model);
		},
		offset: {
			x: -10,
			y: -10
		}
	});
};
