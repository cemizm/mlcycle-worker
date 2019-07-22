
import contiflow

client = contiflow.init()

job = "4c16579d-c297-4554-aa08-78422a0502eb"
step = 2

file = {
    'name': "Test 33",
    'filename': "test2.txt",
    'type': 0
}

#client.Scheduler.claim(job, step)

#with open('requirements.txt') as f:
#    client.Fragments.upload(job, 0, file, f)


steps = [
    { 
        'name': 'Ingest',
        'docker': {
            'image': 'cemizm/tf-benchmark-gpu',
            'command': '--model inception3'
        }
    },
    { 
        'name': 'Prepare',
        'docker': {
            'buildConfiguration': {
                'dockerfile': 'prepare.Dockerfile'
            },
            'command': 'python test'
        }
    }
]

#client.Jobs.addSteps(job, steps)

#client.Scheduler.complete(job, step)

client.Jobs.trigger("8f0282d2-efac-4ea7-ab97-8aaa7ddd987d")
client.Jobs.trigger("61004119-9420-49d4-ab2a-066c88bd6994")
client.Jobs.trigger("8f0282d2-efac-4ea7-ab97-8aaa7ddd987d")