import './chat-thinking-animation.css'; // 引入样式文件

const ChatThinkingAnimation = (({onThoughtChange}) => {

    const handleClick = () => {
        onThoughtChange(prev => !prev);
        console.log('点击了');
    };

    return (
        <div className="thinking-animation" onClick={handleClick} >View thinking process</div>
    )}
);

export default ChatThinkingAnimation;