import React from "react";
import PropTypes from "prop-types";

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
        if (title == null || title == "nan") {
            return "";
        } else {
            return title;
        }
    }

    renderURL() {
        let url = this.props.data.url;
        if (url == null || url == "nan") {
            return <p></p>;
        } else {
            return <a>{url}</a>;
        }
    }

    renderUserBlock() {
        let username = this.props.data.username;
        let userurl = this.props.data.user_url;

        let usernameRen = <p>User: {username}</p>;
        let userURLRen = <a>User URL: {userurl}</a>;

        if (username == null || username == "nan") {
            usernameRen = <p>User: anonymous</p>;
        }

        if (userurl == null || userurl == "nan") {
            userURLRen = <p></p>;
        }

        return (
            <div>
                {usernameRen}
                {userURLRen}
            </div>
        );
    }

    renderDate() {
        let date = this.props.data.created_date;

        if (date == null || date == "nan") {
            return <p></p>;
        } else {
            return <p>{date}</p>;
        }
    }

    renderText() {
        let title = this.props.data.title;
        let text = this.props.data.text;

        if (
            title == null ||
            title == "nan" ||
            title.replace(/(\r\n|\n|\r)/gm, " ").replace("  ", " ") !=
                text.replace(/(\r\n|\n|\r)/gm, " ").replace("  ", " ")
        ) {
            return (
                <div>
                    <hr />
                    {this.renderDate()}
                    <p>{text}</p>
                </div>
            );
        } else {
            return this.renderDate();
        }
    }

    render() {
        if (this.props.data.title == undefined) {
            return <p>{this.props.data.text}</p>;
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
