import React from "react";
import PropTypes from "prop-types";
import moment from 'moment';

class DataViewer extends React.Component {
    constructor(props) {
        super(props);

        this.renderTitle = this.renderTitle.bind(this);
        this.renderURL = this.renderURL.bind(this);
        this.renderUserBlock = this.renderUserBlock.bind(this);
        this.renderText = this.renderText.bind(this);
        this.renderDate = this.renderDate.bind(this);
    }

    renderTitle() {
        let title = this.props.data.title;
        let text = this.props.data.data;

        if (title == null || title == "nan" || title == "" ||
            (title.replace(/(\r\n|\n|\r)/gm, " ").replace("  ", " ") ==
                text.replace(/(\r\n|\n|\r)/gm, " ").replace("  ", " "))) {
            return null;
        } else {
            return title;
        }
    }

    renderURL() {
        let url = this.props.data.url;
        if (url == null || url == "nan" || url == "") {
            return <p></p>;
        } else {
            return <a href={url} target="_blank">{url}</a>;
        }
    }

    renderUserBlock() {
        let username = this.props.data.username;
        let userurl = this.props.data.user_url;

        let userURLRen = <p></p>;
        let userURLName = <p></p>;

        let usernameExists = (username != null && username != "nan" && username != "");
        let userUrlExists = (userurl != null && userurl != "nan" && userurl != "");

        if (userUrlExists) {
            userURLRen = <a href={userurl} target="_blank">{userurl}</a>;
        }

        if (usernameExists) {
            userURLName = <p>{username}</p>;
        }

        if ((!userUrlExists) && (!usernameExists)) {
            return null;
        }

        return (
            <div>
                {userURLName}
                {userURLRen}
                <hr />
            </div>
        );
    }

    renderDate() {
        let date = this.props.data.created_date;

        if (date == null || date == "nan" || date == "") {
            return <p></p>;
        } else {
            return <p id="data_date_p">{moment(date).format("LLLL")}</p>;
        }
    }

    renderText() {
        let text = this.props.data.data;

        return (
            <div>
                {this.renderDate()}
                <p>{text}</p>
            </div>
        );
    }

    render() {

        if (this.props.data.title == undefined) {
            return <p>{this.props.data.data}</p>;
        } else {
            return (
                <div>
                    <div className="panel panel-default">
                        <div className="panel-heading">
                            <h2 className="panel-title">
                                {this.renderTitle()}
                            </h2>
                            {this.renderURL()}
                        </div>
                        <div className="panel-body">
                            {this.renderUserBlock()}
                            {this.renderText()}
                        </div>
                    </div>
                </div>
            );
        }
    }
}

DataViewer.propTypes = {
    data: PropTypes.object
};

export default DataViewer;
