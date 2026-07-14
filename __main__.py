from .app import run_agent

if __name__ == "__main__":
    # query = "Trận đấu tiếp theo của đội tuyển Bồ Đào Nha tại Worldcup là trận nào?"
    # query = "Xu hướng kiến trúc LLM hiện nay là gì?"
    # query = "Hãy nghiên cứu các phương pháp đánh giá cho tác vụ NLP mới nhất hiện nay."
    query = (
        "Hãy nghiên cứu các mô hình BERT-based dành cho tiếng Việt mới nhất hiện nay."
    )
    run_agent(query)
    # test()
