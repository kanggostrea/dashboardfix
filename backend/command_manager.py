class CommandManager:
    def __init__(self):
        self.command_queue = []
        self.command_status = {}

    def queue_command(self, panel_id, command):
        self.command_queue.append({
            'panel_id': panel_id,
            'command': command,
            'status': 'pending'
        })
        self.command_status[command] = 'pending'

    def get_pending_commands(self, panel_id):
        return [cmd for cmd in self.command_queue if cmd['panel_id'] == panel_id and cmd['status'] == 'pending']

    def update_command_status(self, command, status):
        for cmd in self.command_queue:
            if cmd['command'] == command:
                cmd['status'] = status
                self.command_status[command] = status
                break

    def list_commands_with_status(self):
        return [(cmd['command'], cmd['status']) for cmd in self.command_queue]
