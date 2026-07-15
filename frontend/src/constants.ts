declare const __APP_VERSION__: string;

export const APP_NAME = 'PAA Analyzer';
export const APP_VERSION: string = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : 'dev';
