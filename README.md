This [`fabfile.py`](http://docs.fabfile.org/) implemented to deploy
[Sentry](http://sentry.readthedocs.org/) to AWS EC2.
The default setting is specified for PostgreSQL database.

### Usage

Setup your AWS credentials. `~/.boto` would be easy.

```
[Credentials]
aws_access_key_id = <your key>
aws_secret_access_key = <your key>
```

Then, deploy!

```
$ fab setup_sentry
Instances to deploy:
 1. ●running i-1a2s3d4f katsudon
Choose instance(s) [number(s), id(s), name(s), all, done]: 1
 *. ●running i-1a2s3d4f katsudon
Choose instance(s) [number(s), id(s), name(s), all, done]: done
 [my.instance.on.amazonaws.ec2.com] Executing task 'setup_sentry'

 ...

 Done.
```

Recommend you change default user's password just after the time when
the deployment completed.
