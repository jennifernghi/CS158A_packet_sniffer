
import React from 'react';

export default class PacketHeader extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      expanded: false,
    };

    this.toggle = this.toggle.bind(this);
  }

  renderDetail() {
    if (this.state.expanded) {
      return (<div />);
    }

    return null;
  }

  toggle() {
    this.setState({
      expanded: !this.state.expanded,
    });
  }

  render() {
    return (<li className="packet-header">
      <div className="packet-header-summary" onClick={this.toggle}>{this.props.header._summary}</div>
      {this.renderDetail()}
    </li>);
  }
}
