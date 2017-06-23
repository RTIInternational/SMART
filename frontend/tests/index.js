require('app-module-path').addPath(`${__dirname}'./../`);
import Mocha from 'mocha';
import Glob from 'glob';
import './dom';

let pattern = `src/**/*.spec.js`;

const mocha = new Mocha();

Glob(pattern, {}, (err, files) => {
    files.forEach((file) => mocha.addFile(file));
    mocha.run((failures) => {
        process.on('exit', () => {
            process.exit(failures);
        });
    });
});