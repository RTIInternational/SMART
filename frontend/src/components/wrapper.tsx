import React from 'react';

export namespace Wrapper {
    export interface Props {
        children?: React.ReactNode
    }
};

const Wrapper:React.SFC<Wrapper.Props> = (props) => (
    <div>
        <header>
            <h1>SMART</h1>
        </header>
        <main>
            {props.children}
        </main>
    </div>
);

export default Wrapper;