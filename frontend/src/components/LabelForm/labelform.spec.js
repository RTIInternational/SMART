import React, { Component } from "react";
import { shallow } from "enzyme";
import { assert } from "chai";
import LabelForm from "./index";

describe("<LabelForm />", () => {
    describe("render", () => {
        it("renders properly if all props provided", () => {
            const fn = () => {};
            const data = [];
            const message = "";
            const wrapper = shallow(
                <LabelForm
                    data={data}
                    passButton={true}
                    discardButton={true}
                    message={message}
                    discardFunction={fn}
                    labelFunction={fn}
                    skipFunction={fn}
                    labels={data}
                />
            );
        });
    });
});
