import ReactDOM from 'react-dom';
import React from 'react';

import FilterBar from './FilterBar';
import PacketList from './PacketList';


class Application extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      keyword: '',
      jq: false,
    };

    window.jq.onInitialized.addListener(() => this.setState({ jq: true }));
  }

  render() {
    return (
      <div>
        <FilterBar onKeywordChange={keyword => this.setState({ keyword })} loaded={this.state.jq} />
        <PacketList query={this.state.keyword} />
      </div>
    );
  }
}


ReactDOM.render(<Application />, document.getElementById('root'));
