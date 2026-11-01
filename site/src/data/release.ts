import meta from '../../public/data/meta.json';

// The headline year comes from the pipeline output, so a new release needs no page edits.
export const YEAR: number = meta.headline_year;
export const PREV = YEAR - 1;
export const SPAN = `2014–${YEAR}`;
