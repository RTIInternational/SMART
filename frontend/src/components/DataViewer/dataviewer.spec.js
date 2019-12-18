import React, { Component } from "react";
import { shallow } from "enzyme";
import { assert } from "chai";
import DataViewer from "./index";

describe("<DataViewer />", () => {
    describe("render", () => {
        it("renders properly if all props provided", () => {
            const data = [];

            const wrapper = shallow(<DataViewer data={data} />);
        });
    });
});
