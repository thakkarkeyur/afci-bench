/**
 * Frozen path-glob layer assignment.
 *
 * A file's layer is determined by its PATH matched against the frozen layer path
 * globs from the evaluator manifest, never by the module specifier or by a
 * tsconfig the coding model could have edited. This is what makes the direction
 * check tamper-resistant: adding an alias cannot relabel a file's layer.
 */

import { matchAnyGlob } from './glob';
import { LayerDef } from './types';

export class LayerMap {
  private readonly layers: LayerDef[];

  constructor(layers: LayerDef[]) {
    this.layers = layers;
  }

  /** First layer (in manifest order) whose globs match the posix relative path. */
  layerOf(relPath: string): string | null {
    for (const layer of this.layers) {
      if (matchAnyGlob(relPath, layer.path_globs)) {
        return layer.id;
      }
    }
    return null;
  }

  has(layerId: string): boolean {
    return this.layers.some((l) => l.id === layerId);
  }

  ids(): string[] {
    return this.layers.map((l) => l.id);
  }
}
