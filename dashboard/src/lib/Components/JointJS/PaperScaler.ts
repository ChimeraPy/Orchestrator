export class PaperScaler {
	paper: joint.dia.Paper;
	step: number;
	maxZoomLevel: number;
	minZoomLevel: number;

	constructor(paper: joint.dia.Paper, step?: number, maxZoomLevel?: number, minZoomLevel?: number) {
		this.paper = paper;
		this.step = step || 0.25;
		this.maxZoomLevel = maxZoomLevel || 2;
		this.minZoomLevel = minZoomLevel || 0.2;
	}

	zoom(scale: number) {
		this.paper.scale(scale);
		this.paper.fitToContent({
			minWidth: this.paper.options.width,
			minHeight: this.paper.options.height
		} as joint.dia.Paper.FitToContentOptions);
	}

	zoomOut() {
		const scale = this.getPaperScale();
		const wouldBeScale = scale - this.step;
		if (wouldBeScale > this.minZoomLevel) {
			this.zoom(wouldBeScale);
		}
	}

	zoomIn() {
		const scale = this.getPaperScale();
		const wouldBeScale = scale + this.step;
		if (wouldBeScale < this.maxZoomLevel) {
			this.zoom(wouldBeScale);
		}
	}

	scaleContentToFit() {
		this.paper?.scaleContentToFit({
			padding: 50,
			maxScale: this.maxZoomLevel,
			minScale: this.minZoomLevel
		});
	}

	getPaperScale(): number {
		return this.paper.scale().sx;
	}
}
