
import React from 'react';
import Card from '../base/Card';

const ChatWorkspace: React.FC = () => {
    return (
        <Card style={{ height: 'calc(100vh - 100px)', padding: 0, overflow: 'hidden' }}>
            <iframe
                src="http://localhost:8065"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Mattermost Chat"
            />
        </Card>
    );
};

export default ChatWorkspace;
