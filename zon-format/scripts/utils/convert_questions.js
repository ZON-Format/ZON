/**
 * Convert questions from JS format to JSON.
 * 
 * Reads the questions-309.js file from the ZON-TS repository and converts it
 * to a JSON file for use in Python benchmarks.
 */
const fs = require('fs');
const path = require('path');

const jsPath = '/Users/roni/Developer/ZON/ZON-TS/benchmarks/datasets/questions-309.js';
const jsonPath = '/Users/roni/Developer/ZON/zon-format/benchmarks/data/questions_309.json';

const content = fs.readFileSync(jsPath, 'utf8');

const data = (function() {
    let arrayStr = content.replace(/const\s+questions\s*=\s*/, '');
    arrayStr = arrayStr.replace(/module\.exports\s*=\s*\{[\s\S]*\}/, '');
    arrayStr = arrayStr.replace(/;\s*$/, '');
    return eval(arrayStr);
})();

fs.writeFileSync(jsonPath, JSON.stringify(data, null, 2));
console.log(`Converted ${data.length} questions to ${jsonPath}`);
