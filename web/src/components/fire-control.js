import * as React from "react";
import {Button, Row, Col, Input, InputNumber, Slider, Typography, Tabs, message, Table} from 'antd';

const {Text, Paragraph} = Typography;
const {TabPane} = Tabs;

class FireControl extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            actions: undefined,
            checkins: undefined,
            delay: undefined,
            fireDuration: 60,
            token: undefined
        }
    };

    onTokenChange(e) {
        this.setState({
            token: e.target.value
        })
    }

    onChange(e) {
        this.setState({
            fireDuration: e,
        });
    };

    getCheckins() {
        if (this.state.token === undefined) {
            message.error('Token is required.');
            return;
        }
        const requestOptions = {
            method: 'GET',
            headers: {'Authorization': 'Bearer ' + this.state.token},
            // headers: { 'Content-Type': 'application/json' },
            // body: JSON.stringify({ title: 'React POST Request Example' })
        };
        fetch('https://us-east1-baserate-332800.cloudfunctions.net/gull-cannon/checkins', requestOptions)
            .then(response => response.json())
            .then(data => this.setState({checkins: data.checkins}))
            .catch((error) => {
                console.error('Error:', error);
            });
    }

    getStatus(e) {
        if (this.state.token === undefined) {
            message.error('Token is required');
            return;
        }
        const requestOptions = {
            method: 'GET',
            headers: {'Authorization': 'Bearer ' + this.state.token},
        };
        fetch('https://us-east1-baserate-332800.cloudfunctions.net/gull-cannon/actions', requestOptions)
            .then(response => response.json())
            .then(data => this.setState({actions: data.actions, delay: data.delay}))
            .catch((error) => {
                console.error('Error:', error);
            });
    };

    requestFire() {
        if (this.state.token === undefined) {
            message.error('Token is required');
            return;
        }
        const requestOptions = {
            method: 'POST',
            headers: {'Authorization': 'Bearer ' + this.state.token, 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: "fire", "duration": this.state.fireDuration * 1000 })
        };
        fetch('https://us-east1-baserate-332800.cloudfunctions.net/gull-cannon/actions', requestOptions)
            .then(response => response.json())
            .then(data => this.setState({actions: data.actions, delay: data.delay}))
            .catch((error) => {
                console.error('Error:', error);
            });
    }

    render() {
        let action_text = "";
        let callback_text = "";
        const {fireDuration} = this.state;
        if (this.state.actions === undefined) {
            action_text = ""
        } else if (this.state.actions.length === 0) {
            action_text = "No actions scheduled."
        } else {
            action_text = "Actions: \n" + JSON.stringify(this.state.actions)
        }
        if (this.state.delay !== undefined) {
            callback_text = "Current callback frequency: " + (this.state.delay / 1000).toString() + " seconds."
        } else {
            callback_text = ""
        }
        const columns = [
  {
    title: 'Date',
    dataIndex: 'datetime',
  },
  {
    title: 'id',
    dataIndex: 'id',
  }
        ]
        return (
            <>
                <Input placeholder="token" value={this.state.token} onChange={e => this.onTokenChange(e)}/>
                <Tabs defaultActiveKey="1">
                    <TabPane tab="Request Fire" key="1">
                        <Text>Request gull cannon to fire for the specified duration (in seconds).</Text>
                        <Row>
                            <Col span={18}>
                                <Slider
                                    min={30}
                                    max={480}
                                    onChange={e => this.onChange(e)}
                                    value={typeof fireDuration === 'number' ? fireDuration : 60}
                                />
                            </Col>
                            <Col span={6}>
                                <InputNumber
                                    min={30}
                                    max={480}
                                    style={{margin: '0 16px'}}
                                    value={fireDuration}
                                    onChange={e => this.onChange(e)}
                                />
                            </Col>
                        </Row>
                        <Row>
                            <Button type="primary" onClick={e => this.requestFire(e)}>Request Fire</Button>
                        </Row>
                    </TabPane>
                    <TabPane tab="Current Status" key="2">
                        <Paragraph>{action_text}</Paragraph>
                        <Paragraph>{callback_text}</Paragraph>
                        <Button type="primary" onClick={e => this.getStatus(e)}>Get Current Status</Button>
                    </TabPane>
                    <TabPane tab="Recent Checkins" key="3">
                        <Table columns={columns} dataSource={this.state.checkins} />
                        <Button type="primary" onClick={e => this.getCheckins(e)}>Get Recent Checkins</Button>
                    </TabPane>
                </Tabs>

            </>
        )
    };
}

export default FireControl