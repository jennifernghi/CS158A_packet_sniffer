
import React from 'react';
import PropTypes from 'prop-types';

export default class PacketHeader extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      expanded: false,
    };

    this.toggle = this.toggle.bind(this);
  }

  toggle() {
    this.setState({
      expanded: !this.state.expanded,
    });
  }

  renderHeaderAttributes(attributes = this.props.header) {
    return Object.entries(attributes)
      .filter(([key]) => !key.startsWith('_'))
      .map(([key, value]) => {
        if (typeof value === 'object') {
          return this.renderHeaderAttributes(value);
        }
        return (<li key={key}><strong>{key}</strong> <span className="value">{value}</span></li>);
      });
  }

  renderDetail() {
    if (this.state.expanded) {
      return (
        <div className="packet-header-detail">
          <ul>
            {this.renderHeaderAttributes()}
          </ul>
        </div>
      );
    }

    return null;
  }

  render() {
    return (
      <li className="packet-header">
        <div className="packet-header-summary" onClick={this.toggle}>{this.props.header._summary}</div>
        {this.renderDetail()}
      </li>
    );
  }
}

PacketHeader.propTypes = {
  header: PropTypes.object.isRequired,
};
