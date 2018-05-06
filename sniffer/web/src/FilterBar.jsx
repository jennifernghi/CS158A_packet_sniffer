
import React from 'react';
import PropTypes from 'prop-types';

export default class FilterBar extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      keyword: '',
    };

    this.handleChange = this.handleChange.bind(this);
  }

  handleChange(e) {
    this.props.onKeywordChange(this.state.keyword);
    e.preventDefault();
  }

  render() {
    return (
      <div className="filter-bar">
        <form onSubmit={this.handleChange}>
          <input type="text" placeholder="Type your filter here..." onChange={e => this.setState({ keyword: e.target.value })} disabled={!this.props.loaded} />
        </form>
      </div>
    );
  }
}

FilterBar.propTypes = {
  onKeywordChange: PropTypes.func.isRequired,
  loaded: PropTypes.bool.isRequired,
};

