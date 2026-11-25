from server_gruzovichkof_avtoflot import app, PORT


if __name__ == "__main__":
    app.log_service.log_start(PORT)
    app.run()
