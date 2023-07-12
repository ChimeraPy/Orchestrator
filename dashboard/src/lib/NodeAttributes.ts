/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

/**
 * The type of the parameter.
 */
export type AttributeType =
  | "STRING"
  | "INTEGER"
  | "FLOAT"
  | "BOOLEAN"
  | "ARRAY"
  | "TUPLE"
  | "OBJECT"
  | "ENUM"
  | "UNKNOWN";

export interface NodeAttributeMeta {
  /**
   * The name of the parameter.
   */
  name: string;
  /**
   * The default value of the parameter.
   */
  default?: {
    [k: string]: unknown;
  };
  /**
   * The type of the parameter.
   */
  type?: AttributeType;
  /**
   * The choices of the parameter.
   */
  choices?: unknown[];
  /**
   * Whether the parameter is required.
   */
  required?: boolean;
}
