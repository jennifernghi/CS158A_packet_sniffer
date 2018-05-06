import React from 'react';
import Websocket from 'react-websocket';

import PacketDetail from './PacketDetail.jsx';

export default class PacketList extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      packets: [],
      selected: null,
    };

    this.handleClick = this.handleClick.bind(this);
  }

  handleData(data) {
    let packets = JSON.parse(data);
    console.log(packets);
    this.setState({
      packets: [...this.state.packets, ...packets]
    });
  }

  handleClick(key) {
    this.setState({
      selected: this.state.selected == key ? null : key,
    });
  }

  renderPacketList() {
    return this.state.packets.slice(-1000).map((packet, index) => {
      const header = packet.headers[packet.headers.length-1]
      return (
      <tr
        className={"packet" + (this.state.selected === packet.id ? " selected" : "")}
        key={packet.id}
        onClick={() => this.handleClick(packet.id)}
      >
        <td>{packet.id}</td>
        <td>{packet.timestamp}</td>
        <td>{packet.name}</td>
        <td>{packet.source}</td>
        <td>{packet.destination}</td>
        <td>{packet.info}</td>
      </tr>);
    });
  }

  renderPacketDetail() {
    if (this.state.selected) {
      return (<PacketDetail packet={this.state.packets[this.state.selected]} />);
    }
    return null;
  }

  render() {
    return (<div className="packet-list-panel">
      <Websocket url={`ws://${location.host}/ws`} onMessage={this.handleData.bind(this)} />
      <table
        className={"packet-list" + (this.state.selected ? " selected" : "")}
        cellSpacing="0"
        cellPadding="0"
      >
        <thead>
          <tr>
            <th width="3%">&#35;</th>
            <th width="15%">Time</th>
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
      {this.renderPacketDetail()}
    </div>);
  }
}
