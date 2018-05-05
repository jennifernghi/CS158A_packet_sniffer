import ReactDOM from 'react-dom';
import React from 'react';

import FilterBar from './FilterBar.jsx';
import PacketList from './PacketList.jsx';

ReactDOM.render(
  (<div>
    <FilterBar />
    <PacketList />
  </div>),
  document.getElementById('root')
);
