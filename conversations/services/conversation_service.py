import os
import asyncio
from typing import List, Dict, Any, Optional
from django.conf import settings

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# LangGraph imports
from langgraph.graph import StateGraph, END

# Sentiment analysis
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Sync version of the conversation agent
def conversation_agent(user, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Process user message and generate response using LangChain and LangGraph
    
    Args:
        user: Django user object
        message: User's message text
        history: List of conversation history messages
    
    Returns:
        Dict containing assistant response and metadata
    """
    # Set up the LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY
    )
    
    # Define system message template based on user's mood tracking
    system_template = """
    당신은 사용자에게 정서적 지원과 공감을 제공하는 친절한 상담 도우미입니다. 
    사용자의 감정 상태를 고려하여 적절한 어조와 말투로 응답하세요.
    항상 공감적이고, 판단하지 않으며, 따뜻한 어조를 유지하세요.
    
    다음 지침을 따르세요:
    1. 사용자의 감정을 인정하고 정상화하세요.
    2. 개방형 질문을 통해 사용자가 자신의 감정을 탐색하도록 돕습니다.
    3. 필요한 경우 긍정적인 관점을 제시하되, 무시하거나 가볍게 여기지 마세요.
    4. 사용자의 대화 내용에 맞는 실용적인 조언이나 대처 전략을 제공할 수 있습니다.
    5. 사용자가 너무 부정적인 생각에 빠져있다면 긍정적인 방향으로 생각을 전환할 수 있도록 도와주세요.
    
    중요: 당신은 전문 정신건강 제공자가 아니며, 심각한 정신건강 위기에 처한 사용자에게는 전문가에게 도움을 구하도록 권장해야 합니다.
    자살이나 자해에 관한 언급이 있으면 즉시 정신건강 긴급전화(1393)나 가까운 정신건강의학과 의사를 찾도록 안내하세요.
    """
    
    # Create system message
    system_message = SystemMessage(content=system_template)
    
    # Prepare conversation history
    messages = [system_message]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    
    # Add current user message
    messages.append(HumanMessage(content=message))
    
    # Define our LangGraph nodes
    
    # 1. Analyze user sentiment
    def analyze_sentiment(state):
        sentiment_prompt = PromptTemplate.from_template(
            """사용자 메시지에서 감정 상태를 분석하세요.
            
            메시지: {message}
            
            1에서 5까지의 점수로 사용자의 기분을 평가해 주세요:
            1: 매우 우울하거나 부정적
            2: 약간 우울하거나 부정적
            3: 중립적
            4: 약간 긍정적
            5: 매우 긍정적이거나 행복함
            
            이유를 간략히 설명하고 점수만 알려주세요:
            """
        )
        
        sentiment_chain = LLMChain(llm=llm, prompt=sentiment_prompt)
        result = sentiment_chain.run(message=message)
        
        # Extract just the numeric score
        try:
            score_text = result.strip()
            # Find the score (1-5) in the response
            import re
            score_match = re.search(r'[1-5]', score_text)
            if score_match:
                score = int(score_match.group(0))
            else:
                # Default to neutral if we can't extract a score
                score = 3
        except Exception:
            score = 3
        
        # Convert to a -1 to 1 scale for sentiment
        sentiment_score = (score - 3) / 2
        
        state["sentiment_score"] = sentiment_score
        return state
    
    # 2. Check for crisis indicators
    def check_crisis_indicators(state):
        crisis_prompt = PromptTemplate.from_template(
            """사용자의 메시지에서 정신 건강 위기 징후가 있는지 확인하세요.
            
            메시지: {message}
            
            다음 항목을 확인하고 '있음' 또는 '없음'으로 응답하세요:
            1. 자살이나 자해 생각 언급
            2. 타인을 해치려는 생각 언급
            3. 심각한 정신적 고통이나 위기 징후
            
            응답 형식: 위기 징후 있음/없음
            """
        )
        
        crisis_chain = LLMChain(llm=llm, prompt=crisis_prompt)
        result = crisis_chain.run(message=message)
        
        # Check if crisis indicators were detected
        has_crisis = "있음" in result
        
        state["has_crisis"] = has_crisis
        return state
    
    # 3. Generate appropriate response
    def generate_response(state):
        # If crisis indicators detected, include crisis resources
        if state.get("has_crisis", False):
            response_prompt = PromptTemplate.from_template(
                """사용자가 정신 건강 위기를 겪고 있는 것 같습니다. 다음 지침에 따라 응답하세요:
                
                1. 사용자의 감정을 인정하고 공감을 표현하세요.
                2. 전문적인 도움을 구하는 것의 중요성을 강조하세요.
                3. 다음 위기 자원을 포함하세요:
                   - 자살예방상담전화: 1393 (24시간 운영)
                   - 정신건강 위기상담전화: 1577-0199
                4. 비판적이거나 판단하지 않는 태도를 유지하세요.
                
                사용자의 메시지: {message}
                """
            )
        else:
            # Use sentiment score to adjust response tone
            sentiment_score = state.get("sentiment_score", 0)
            
            if sentiment_score < -0.5:  # Very negative
                response_prompt = PromptTemplate.from_template(
                    """사용자가 매우 부정적인 감정을 표현하고 있습니다. 다음 지침을 따르세요:
                    
                    1. 사용자의 감정을 충분히 인정하고 공감하세요.
                    2. 점진적으로 관점 전환을 도울 수 있는 질문이나 제안을 제공하세요.
                    3. 작은 긍정적 단계를 제안하되, 감정을 가볍게 여기지 마세요.
                    4. 필요하다면 전문가의 도움을 권유하세요.
                    
                    사용자의 메시지: {message}
                    """
                )
            elif sentiment_score < 0:  # Somewhat negative
                response_prompt = PromptTemplate.from_template(
                    """사용자가 다소 부정적인 감정을 표현하고 있습니다. 다음 지침을 따르세요:
                    
                    1. 사용자의 감정을 인정하고 공감하세요.
                    2. 상황을 다른 관점에서 볼 수 있는 방법을 제안하세요.
                    3. 실용적인 대처 전략이나 문제 해결 접근 방식을 제안하세요.
                    
                    사용자의 메시지: {message}
                    """
                )
            elif sentiment_score > 0.5:  # Very positive
                response_prompt = PromptTemplate.from_template(
                    """사용자가 매우 긍정적인 감정을 표현하고 있습니다. 다음 지침을 따르세요:
                    
                    1. 사용자의 긍정적인 감정을 함께 기뻐하고 강화하세요.
                    2. 이러한 긍정적인 상태를 유지하거나 더 발전시킬 수 있는 방법을 제안하세요.
                    3. 앞으로의 긍정적인 계획이나 목표에 대해 질문하세요.
                    
                    사용자의 메시지: {message}
                    """
                )
            elif sentiment_score > 0:  # Somewhat positive
                response_prompt = PromptTemplate.from_template(
                    """사용자가 다소 긍정적인 감정을 표현하고 있습니다. 다음 지침을 따르세요:
                    
                    1. 사용자의 긍정적인 측면을 인정하고 격려하세요.
                    2. 이러한 긍정적인 요소를 더 발전시킬 수 있는 방법을 제안하세요.
                    3. 개방형 질문으로 대화를 이어가세요.
                    
                    사용자의 메시지: {message}
                    """
                )
            else:  # Neutral
                response_prompt = PromptTemplate.from_template(
                    """사용자가 중립적인 감정을 표현하고 있습니다. 다음 지침을 따르세요:
                    
                    1. 사용자의 상황이나 생각을 더 깊이 탐색할 수 있는 개방형 질문을 하세요.
                    2. 공감적이고 지지적인 태도를 유지하세요.
                    3. 사용자가 자신의 생각과 감정을 더 명확히 이해할 수 있도록 돕는 관점을 제공하세요.
                    
                    사용자의 메시지: {message}
                    """
                )
        
        response_chain = LLMChain(llm=llm, prompt=response_prompt)
        response_content = response_chain.run(message=message)
        
        state["response"] = {
            "content": response_content,
            "sentiment_score": state.get("sentiment_score", 0),
            "has_crisis": state.get("has_crisis", False)
        }
        return state
    
    # Build LangGraph
    workflow = StateGraph(state_type=Dict)
    
    # Add nodes
    workflow.add_node("analyze_sentiment", analyze_sentiment)
    workflow.add_node("check_crisis", check_crisis_indicators)
    workflow.add_node("generate_response", generate_response)
    
    # Set up the edges
    workflow.set_entry_point("analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "check_crisis")
    workflow.add_edge("check_crisis", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Compile and run the graph
    app = workflow.compile()
    result = app.invoke({"message": message})
    
    return result["response"]

# Async version of the conversation agent
async def conversation_agent_async(user, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Async wrapper for the conversation agent"""
    # Use run_in_executor to run the synchronous function in a thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, conversation_agent, user, message, history)
