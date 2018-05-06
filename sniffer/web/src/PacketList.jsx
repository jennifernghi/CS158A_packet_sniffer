import React from 'react';
import PropTypes from 'prop-types';
import Websocket from 'react-websocket';

import PacketDetail from './PacketDetail';


export default class PacketList extends React.Component {
  static getDerivedStateFromProps(nextProps, prevState) {
    if (!nextProps.query) return {};
    const flags = PacketList.filterPacketWithQuery(prevState.packets, nextProps.query);

    if (flags.length !== 0) {
      return { flags };
    }

    return {};
  }

  static filterPacketWithQuery(packets, query) {
    try {
      const result = window.jq(packets, `[.[] | ${query} | not | not]`);

      if (result) {
        return result;
      }
      return [];
    } catch (error) {
      console.error(error);
      return [];
    }
  }

  constructor(props) {
    super(props);
    this.state = {
      packets: [],
      raws: [],
      selected: null,
      flags: [],
    };

    this.handleClick = this.handleClick.bind(this);
    this.handleData = this.handleData.bind(this);
  }

  handleData(data) {
    const packets = JSON.parse(data);
    const raws = packets.map(({ raw }) => raw);
    const strippedPacket = packets.map((packet) => {
      const result = packet;
      delete result.raw;
      return result;
    });

    const nextState = {
      raws: this.state.raws.concat(raws),
      packets: this.state.packets.concat(strippedPacket),
    };

    if (this.props.query) {
      const flags = PacketList.filterPacketWithQuery(strippedPacket, this.props.query);
      nextState.flags = this.state.flags.concat(flags);
    }

    this.setState(nextState);
  }

  handleClick(key) {
    this.setState({
      selected: this.state.selected === key ? null : key,
    });
  }

  renderPacketList() {
    let packets;

    if (this.state.flags.length === this.state.packets.length) {
      packets = this.state.packets.filter((_, index) => this.state.flags[index]);
    } else {
      ({ packets } = this.state);
    }

    return packets.slice(-1000).map(packet => (
      <tr
        className={`packet ${this.state.selected === packet.id ? 'selected' : ''}`}
        key={packet.id}
        onClick={() => this.handleClick(packet.id)}
      >
        <td>{packet.id}</td>
        <td>{packet.timestamp}</td>
        <td>{packet.type}</td>
        <td>{packet.source}</td>
        <td>{packet.destination}</td>
        <td>{packet.info}</td>
      </tr>
    ));
  }

  renderPacketDetail() {
    if (this.state.selected) {
      const index = this.state.selected - this.state.packets[0].id;
      return (<PacketDetail packet={this.state.packets[index]} raw={this.state.raws[index]} />);
    }
    return null;
  }

  render() {
    return (
      <div className="packet-list-panel">
        <Websocket url={`ws://${window.location.host}/ws`} onMessage={this.handleData} />
        <table
          className={`packet-list ${this.state.selected ? 'selected' : ''}`}
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
      </div>
    );
  }
}

PacketList.propTypes = {
  query: PropTypes.string,
};

PacketList.defaultProps = {
  query: '',
};
