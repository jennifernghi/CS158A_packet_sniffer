import React from 'react';
import Websocket from 'react-websocket';

import PacketDetail from './PacketDetail.jsx';

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
    return this.state.packets.slice(-1000).map((packet, index) => {
      const header = packet.headers[packet.headers.length-1]
      return (<tr className="packet" key={index}>
        <td>{packet.id}</td>
        <td>{packet.timestamp}</td>
        <td>{packet.name}</td>
        <td>{packet.source}</td>
        <td>{packet.destination}</td>
        <td>{packet.info}</td>
      </tr>);
    });
  }

  render() {
    return (<div className="packet-list-panel">
      <Websocket url={`ws://${location.host}/ws`} onMessage={this.handleData.bind(this)} />
      <table className="packet-list">
        <thead>
          <tr>
            <th width="3%">&#35;</th>
            <th width="15%">Timestamp</th>
            <th width="10%">Type</th>
            <th width="15%">Source</th>
            <th width="15%">Destination</th>
            <th>Info</th>
          </tr>
        </thead>
        <tbody>
          {this.renderPacketList()}
        </tbody>
      </table>
      <PacketDetail />
    </div>);
  }
}
