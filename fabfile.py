# coding=utf8
from fabric.api import *
from fabric.colors import *
from boto import ec2
from utc import now


AWS_REGION = 'ap-northeast-1' # Tokyo


conn = ec2.connect_to_region(AWS_REGION)
instances = None


env.user = 'ubuntu'


def _get_all_instances():
    global instances
    if instances is not None:
        return instances
    results = conn.get_all_instances()
    instances = []
    for r in results:
        for instance in r.instances:
            instances.append(instance)
    return instances


def list_instances(state=None, selected_ids=set()):
    instances = _get_all_instances()
    if state is not None:
        instances = [i for i in instances if i.state == state]
    for i_, instance in enumerate(instances):
        if instance.id in selected_ids:
            number = blue(' *')
        else:
            number = '{0:2d}'.format(i_ + 1)
        if instance.state == 'running': 
            state = green('●running')
        else:
            state = red('●unable')
        id_ = cyan(instance.id)
        name = magenta(instance.tags['Name'])
        print '{0}. {1} {2} {3}'.format(number, state, id_, name)
    return instances


def parse_hosts():
    instances = _get_all_instances()
    instances = [i for i in instances if i.state == 'running']
    hosts = []
    for host in env.hosts:
        for instance in instances:
            if host in (instance.tags['Name'],
                        instance.public_dns_name,
                        instance.ip_address,
                        instance.private_dns_name,
                        instance.private_ip_address):
                hosts.append(instance.public_dns_name)
    return hosts


def get_hosts():
    print 'Instances to deploy:'
    selected = set()
    while True:
        instances = list_instances(state='running',
                                   selected_ids=[instance.id
                                                 for instance in selected])
        input_ = raw_input('Choose instance(s) [number(s), id(s), name(s), '
                           'all, done]: ')
        input_ = input_.lower().strip()
        if input_ == 'done':
            break
        elif input_ == 'all':
            selected.update(instances)
            break
        else:
            for i_, instance in enumerate(instances):
                if any([s in (str(i_ + 1), instance.id, instance.tags['Name'])
                        for s in [s.strip() for s in input_.split(',')]]):
                    selected.add(instance)
    hosts = [instance.public_dns_name for instance in selected]
    return hosts


if env.hosts:
    env.hosts = parse_hosts()
else:
    env.hosts = get_hosts()


def current_instance():
    for instance in _get_all_instances():
        addrs = (instance.public_dns_name, instance.ip_address,
                 instance.private_dns_name, instance.private_ip_address)
        if env.host in addrs:
            return instance
    raise LookupError('cannot found current instance: ' + repr(env.host))


def virtualenv_run(command, env, pty=True):
    run('source {0}/bin/activate && {1}'.format(env, command), pty=pty)


def setup_sentry():
    instance = current_instance()
    instance.add_tag('Status', 'deploy')
    instance.add_tag('StatusDetail', 'setup_sentry')
    run('sudo apt-get install -y build-essential python python-dev python-pip '
         'python-virtualenv python-setuptools libevent-dev supervisor nginx '
         'postgresql postgresql-server-dev-all')
    run('sudo -u postgres createuser -D -S -R sentry')
    run('sudo -u postgres createdb -O sentry sentry')
    run('sudo -u postgres psql -c '
        '"alter user sentry with encrypted password \'sentry\'"')
    put('deploy/sentry.conf.py', '/home/ubuntu/sentry.conf.py')
    run('echo -e "SENTRY_KEY = \'`openssl rand -hex 8`\'" >> '
        '/home/ubuntu/sentry.conf.py')
    run('sudo -u ubuntu mkdir -p /home/ubuntu/sentry')
    run('virtualenv --distribute /home/ubuntu/sentry')
    with cd('/home/ubuntu/sentry'):
        ve = lambda cmd: virtualenv_run(cmd, env='/home/ubuntu/sentry')
        ve('pip install psycopg2 gevent sentry nydus')
        ve('sentry --config=/home/ubuntu/sentry.conf.py upgrade --noinput')
        ve('echo "from django.contrib.auth.models import User; '
           'User.objects.create_superuser(\'sentry\', '
           '\'admin@your.domain.com\', \'sentry\')" | '
           'sentry --config=/home/ubuntu/sentry.conf.py shell')
        ve('sentry --config=/home/ubuntu/sentry.conf.py '
           'repair --owner=sentry')
        put('deploy/sentry.supervisord.conf',
            '/home/ubuntu/sentry.supervisord.conf')
        ve('sudo cp /home/ubuntu/sentry.supervisord.conf '
           '/etc/supervisor/conf.d/sentry.conf')
        ve('sudo supervisorctl update')
    run('sudo touch /etc/nginx/sites-enabled/sentry')
    run('sudo unlink /etc/nginx/sites-enabled/sentry')
    put('deploy/sentry.nginx.conf', '/home/ubuntu/sentry.nginx.conf')
    run('sudo cp /home/ubuntu/sentry.nginx.conf '
        '/etc/nginx/sites-available/sentry.conf')
    run('sudo ln -s /etc/nginx/sites-available/sentry.conf '
        '/etc/nginx/sites-enabled/sentry.conf')
    run('sudo /etc/init.d/nginx restart')
    instance.add_tag('Status', 'work')
    instance.remove_tag('StatusDetail')
    instance.add_tag('DeployedAt', now().strftime('%Y-%m-%d %H:%M:%S'))
