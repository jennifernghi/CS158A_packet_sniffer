
import React from 'react';

export default class PacketDetail extends React.Component {
  renderPacketRaw() {
    const raw = this.props.packet.raw;
    const length = 16;
    const result = [];

    for (let i = 0; i < Math.ceil(raw.length / length); i+= 1) {
      const address = ("0000" + (i * length).toString(16)).substr(-4);
      const hexes = raw.slice(i*length, i*length+length);
      const hex_string = hexes.map((x) => ("00" + x.toString(16)).substr(-2));
      const ascii = hexes.map((x) => x < 127 && x > 31 ? String.fromCharCode(x) : ".").join("");

      result.push(address + ": " + hex_string.join(" ") + "   ".repeat(length - hexes.length) + "    " + ascii);
    }

    return (<pre>{result.join("\n")}</pre>);
  }

  render() {
    return (<div className="packet-detail">
      <div className="packet-attributes">
        <h2>Packet Headers</h2>
      </div>
      <div className="packet-raw">
        <h2>Raw Packets</h2>
        {this.renderPacketRaw()}
      </div>
    </div>);
  }
}
