import type {ValidationError, JSONValue} from 'svelte-jsoneditor';
import {ValidationSeverity} from 'svelte-jsoneditor';

export class NodeKwargsValidator {
		kwargs: any|null;
		constructor(kwargs: any|null) {
			this.kwargs = kwargs;
		}

        setKwargs(kwargs: any|null) {
            this.kwargs = kwargs;
        }

		validate(content: JSONValue): ValidationError[] {
            const missing = Object
				.entries(this.kwargs)
				.filter(([key, value]) => !(key in content as any))
				.map(([key, value]) => {
					return {
						path: [],
						message: `Missing required key ${key} in kwargs`,
						severity: ValidationSeverity.error
					};
			});

			const extra = Object
				.entries(content as any)
				.filter(([key, value]) => !(key in this.kwargs))
				.map(([key, value]) => {
					return {
						path: [key],
						message: `Extra key ${key} in kwargs`,
						severity: ValidationSeverity.error
					}
				});

			return missing.concat(extra);
		}
	}
