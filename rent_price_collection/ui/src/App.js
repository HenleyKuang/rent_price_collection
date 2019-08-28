import React, { Component } from 'react'
import { Button, Col, CustomInput, Form, FormGroup, FormText, Input, InputGroup, InputGroupAddon, Label, Modal, ModalHeader, ModalBody, ModalFooter, Row } from 'reactstrap';
import ReactTable from "react-table"
import $ from 'jquery'

import 'react-table/react-table.css'
import './App.css'

class App extends Component {
  constructor(props) {
    super(props)

    this.state = {
        apiResponse: [],
        loading: false,
        filter: [],
        formFilter: {
          city: "",
          state: "",
          zip_code: "",
          beds: "All",
          baths: "All",
          street_address: "",
        },
        formSortBy: "date_updated",
        formSortDesc: true,
        modal: false,
        pages: -1,
        sortBy: "date_updated",
        sortDesc: true,
    };

    this.searchApi = this.searchApi.bind(this)
    this.toggle = this.toggle.bind(this)
    this.getFilters = this.getFilters.bind(this)
    this.setFilters = this.setFilters.bind(this)
    this.onChangeFormFilter = this.onChangeFormFilter.bind(this)
    this.handleSortByChange = this.handleSortByChange.bind(this)
  }

  componentDidMount() {
    this.getFilters()
    this.toggle()
  }

  searchApi(pageIndex) {
    this.setState({apiResponse: [], loading: true})
    let searchFilters = []
    for( let idx in this.state.filter) {
      let filter = this.state.filter[idx]
      let name = filter.id
      let value = filter.value
      searchFilters.push(name + "=" + value)
    }
    const offsetValue = pageIndex*20
    searchFilters.push("offset=" + offsetValue.toString())
    searchFilters.push("sortby=" + this.state.sortBy)
    if (this.state.sortDesc) {
      searchFilters.push("sortdesc=" + this.state.sortDesc)
    }
    const api_url = '//127.0.0.1:8081/search?' + searchFilters.join("&")
    console.log(api_url)
    $.getJSON (api_url)
        .then(( results ) =>
          this.setState({
            apiResponse: results["listings"],
            loading: false,
            pages: Math.ceil(results["count"]/20),
          }))
  }

  getFilters() {
    let inputFilters = {}
    for( let idx in this.state.filter) {
      let filter = this.state.filter[idx]
      let name = filter.id
      let value = filter.value
      inputFilters[name] = value
    }
    this.setState({
      formFilter: inputFilters,
      formSortBy: this.state.sortBy,
      formSortDesc: this.state.sortDesc,
    })
  }

  setFilters() {
    let searchFilters = []
    for( let name in this.state.formFilter) {
      let value = this.state.formFilter[name]
      searchFilters.push({
        id: name,
        value: value,
      })
    }
    this.setState({
      filter: searchFilters,
      sortBy: this.state.formSortBy,
      sortDesc: this.state.formSortDesc,
    })
  }

  onChangeFormFilter(name, value) {
    let filterCopy = this.state.formFilter
    filterCopy[name] = value
    this.setState({formFilter: filterCopy})
  }

  handleSortByChange (changeEvent) {
    console.log(changeEvent.target.value)
    this.setState({formSortBy: changeEvent.target.value})
  }

  toggle() {
    this.setState(prevState => ({
      modal: !prevState.modal
    }))
  }

  render() {
    let apiStatusData = this.state.apiResponse
    const columns = [
      {
        id: 'source',
        Header: "Source",
        accessor: data => { return data },
        Cell: props => <a href={props.value.url} target="_blank" rel="noopener noreferrer">{props.value.source}</a>,
        width: 90,
      }, {
        id: 'street_address',
        Header: 'Address',
        accessor: 'street_address',
      }, {
        id: 'city',
        Header: 'City',
        accessor: 'city',
      }, {
        id: 'state',
        Header: 'State',
        accessor: 'state',
        width: 40,
      }, {
        id: 'zip_code',
        Header: 'Zip',
        accessor: 'zip_code',
        width: 80,
      }, {
        id: 'beds',
        Header: 'Beds',
        accessor: 'beds',
      }, {
        id: 'baths',
        Header: 'Baths',
        accessor: 'baths',
      }, {
        id: 'sqft',
        Header: 'Sq Ft',
        accessor: 'sqft',
      }, {
        id: 'price',
        Header: 'Price',
        accessor: 'price',
      }, {
        id: 'date_collected',
        Header: 'Date Collected',
        accessor: 'date_collected',
      }, {
        id: 'date_updated',
        Header: 'Date Updated',
        accessor: 'date_updated',
      }, {
        id: 'time_to_market',
        Header: 'Time to Market',
        accessor: data => { return data },
        Cell: props => {
          const date1 = new Date(props.value.date_collected)
          const date2 = new Date(props.value.date_updated)
          const diffTime = Math.abs(date2.getTime() - date1.getTime())
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
          return diffDays
        },
      },
    ]

    return (
      <div className="App">
        <Row className="bg-dark">
          <Col className="text-left">
            <h4 className="strong text-light m-2">
              Rental Listing History
            </h4>
          </Col>
          <Col className="text-right">
            <Button className="m-2" color="primary" onClick={() => {this.toggle(); this.getFilters() }}>Search</Button>
          </Col>
        </Row>
        <Modal isOpen={this.state.modal} toggle={this.toggle} className={this.props.className}>
          <ModalHeader toggle={this.toggle}>Search</ModalHeader>
          <ModalBody>
            <Form>
              <FormGroup>
                <FormText color="muted">
                  Welcome to RentComps where you can search current and past rental listings in your area.
                </FormText>
              </FormGroup>
              <Label>Search By:</Label>
              <Row form>
                <Col md={7}>
                  <FormGroup>
                    <Input type="text" name="city" id="formFilterCity" placeholder="City"
                           value={this.state.formFilter.city} onChange={e => this.onChangeFormFilter("city", e.target.value)}/>
                  </FormGroup>
                </Col>
                <Col md={5}>
                  <FormGroup>
                    <Input type="text" name="state" id="formFilterState" placeholder="State"
                           value={this.state.formFilter.state} onChange={e => this.onChangeFormFilter("state", e.target.value)}/>
                  </FormGroup>
                </Col>
              </Row>
              <FormGroup>
                <FormText color="muted">OR</FormText>
              </FormGroup>
              <Row form>
                <Col md={12}>
                  <FormGroup>
                    <Input type="text" name="zip_code" id="formFilterZip" placeholder="Zipcode"
                           value={this.state.formFilter.zip_code} onChange={e => this.onChangeFormFilter("zip_code", e.target.value)}/>
                  </FormGroup>
                </Col>
              </Row>
              <Label>Filter By:</Label>
              <Row form>
                <Col md={6}>
                  <FormGroup>
                    <InputGroup>
                      <InputGroupAddon addonType="prepend">Beds</InputGroupAddon>
                      <Input type="select" name="beds" id="formFilterSelectBeds"
                             value={this.state.formFilter.beds} onChange={e => this.onChangeFormFilter("beds", e.target.value)}>
                        <option value="">All</option>
                        <option>1</option>
                        <option>2</option>
                        <option>3</option>
                        <option>4</option>
                        <option>5</option>
                        <option>6</option>
                        <option>7</option>
                        <option>8</option>
                        <option>9</option>
                        <option>10</option>
                      </Input>
                    </InputGroup>
                  </FormGroup>
                </Col>
                <Col md={6}>
                  <FormGroup>
                    <InputGroup>
                      <InputGroupAddon addonType="prepend">Baths</InputGroupAddon>
                      <Input type="select" name="baths" id="formFilterSelectBaths"
                             value={this.state.formFilter.baths} onChange={e => this.onChangeFormFilter("baths", e.target.value)}>
                        <option value="">All</option>
                        <option>1</option>
                        <option>2</option>
                        <option>3</option>
                        <option>4</option>
                        <option>5</option>
                        <option>6</option>
                        <option>7</option>
                        <option>8</option>
                        <option>9</option>
                        <option>10</option>
                      </Input>
                    </InputGroup>
                  </FormGroup>
                </Col>
              </Row>
              <Row form>
                <Col md={12}>
                  <FormGroup>
                    <Input type="text" name="street" id="formFilterStreet" placeholder="Street"
                           value={this.state.formFilter.street_address} onChange={e => this.onChangeFormFilter("street_address", e.target.value)}/>
                  </FormGroup>
                </Col>
              </Row>
              <Label>Sort By:</Label>
              <FormGroup>
                <CustomInput type="radio" id="formFilterSortByBeds" name="formFilterSortBy" label="Beds" value="beds"
                             onChange={this.handleSortByChange} checked={this.state.formSortBy === 'beds'} inline />
                <CustomInput type="radio" id="formFilterSortByBaths" name="formFilterSortBy" label="Baths" value="baths"
                             onChange={this.handleSortByChange} checked={this.state.formSortBy === 'baths'} inline />
                <CustomInput type="radio" id="formFilterSortByPrice" name="formFilterSortBy" label="Price" value="price"
                             onChange={this.handleSortByChange} checked={this.state.formSortBy === 'price'} inline />
                <CustomInput type="radio" id="formFilterSortByDate" name="formFilterSortBy" label="Date" value="date_updated"
                             onChange={this.handleSortByChange} checked={this.state.formSortBy === 'date_updated'} inline />
              </FormGroup>
            </Form>
          </ModalBody>
          <ModalFooter>
            <Button color="primary" onClick={async () => { await this.setFilters(); this.toggle(); this.searchApi(0) }}>Search</Button>
            <Button color="secondary" onClick={this.toggle}>Cancel</Button>
          </ModalFooter>
        </Modal>
        <ReactTable
          manual
          className="-striped"
          defaultSortDesc={true}
          pages={this.state.pages}
          loading={this.state.loading}
          pageSize={20}
          minRows={0}
          showPageSizeOptions={false}
          NoDataComponent={() => null}
          style={{fontSize: '12px'}}
          data={apiStatusData}
          defaultSorted={[
            {
              id: this.state.sortBy,
              desc: this.state.sortDesc,
            }
          ]}
          defaultFilterMethod={(filter, row) => apiStatusData}
          onPageChange={(pageIndex) => this.searchApi(pageIndex)}
          onSortedChange={async (newSorted, column, shiftKey) => {await this.setState({"sortBy": newSorted[0].id, "sortDesc": newSorted[0].desc}); this.searchApi(0)}}
          columns={columns}
        />
      </div>
    );
  }
}

export default App;
