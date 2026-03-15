from rag_engine import IndustrialRAG
import time

def test_multiturn():
    print("=== Multi-Turn Conversation Test ===\n")
    engine = IndustrialRAG()
    
    # Simulate Session History
    history = []
    
    # --- Turn 1 ---
    q1 = "如何使用TCP-UDP网络调试助手配置IP和端口？"
    print(f"\n🟢 [Turn 1] User: {q1}")
    
    # 1. Rewrite (No history yet)
    rewritten_q1 = engine.rewrite_query(history, q1)
    
    # 2. Retrieve
    docs1 = engine.retrieve(rewritten_q1, top_k=3)
    doc_name1 = docs1[0].metadata.get('filename') if docs1 else "None"
    print(f"   -> Retrieved: {doc_name1}")
    
    # 3. Simulate Answer (Mock)
    a1 = "您可以在网络设置中输入IP地址和端口号，然后点击连接。"
    history.append({"role": "user", "content": q1})
    history.append({"role": "assistant", "content": a1})
    
    time.sleep(1)

    # --- Turn 2 (Topic Switch) ---
    q2 = "那AccessPort怎么用呢？" # Explicit switch
    print(f"\n🟢 [Turn 2] User: {q2}")
    
    rewritten_q2 = engine.rewrite_query(history, q2)
    docs2 = engine.retrieve(rewritten_q2, top_k=3)
    doc_name2 = docs2[0].metadata.get('filename') if docs2 else "None"
    print(f"   -> Retrieved: {doc_name2}")
    
    a2 = "AccessPort是一款串口调试工具，可以用于监控串口数据。"
    history.append({"role": "user", "content": q2})
    history.append({"role": "assistant", "content": a2})
    
    time.sleep(1)

    # --- Turn 3 (Implicit Reference - The Real Test) ---
    q3 = "它能拦截数据吗？" # "它" refers to AccessPort
    print(f"\n🟢 [Turn 3] User: {q3}")
    
    rewritten_q3 = engine.rewrite_query(history, q3)
    # Expect rewrite: "AccessPort能拦截数据吗？"
    
    docs3 = engine.retrieve(rewritten_q3, top_k=3)
    doc_name3 = docs3[0].metadata.get('filename') if docs3 else "None"
    print(f"   -> Retrieved: {doc_name3}")
    
    if "AccessPort" in rewritten_q3 or "AccessPort" in doc_name3:
        print("\n✅ Test Passed: Successfully resolved reference '它' to 'AccessPort'")
    else:
        print("\n❌ Test Failed: Context lost.")

if __name__ == "__main__":
    test_multiturn()
