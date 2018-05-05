import React from 'react';
import Websocket from 'react-websocket';

export default class PacketList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      packets: [],
    };
  }

  handleData(data) {
    let packets = JSON.parse(data);
    this.setState({
      packets: [...this.state.packets, ...packets]
    });
  }

  renderPacketList() {
    return this.state.packets.map((packet, index) => {
      return (<li className="packet" key={index}>
        <p>{packet.source} => {packet.destination}</p>
      </li>);
    });
  }

  render() {
    return (<div>
      <Websocket url={`ws://${location.host}/ws`} onMessage={this.handleData.bind(this)} />
      <ul className="packet-list">
        {this.renderPacketList()}
      </ul>
    </div>);
  }
}
