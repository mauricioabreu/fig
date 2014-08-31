from __future__ import unicode_literals
from __future__ import absolute_import

import docker
import mock
from .. import unittest

from fig import Service
from fig.container import Container
from fig.service import (
    BuildError,
    ConfigError,
    split_port,
)


class ServiceTest(unittest.TestCase):

    def setUp(self):
        self.mock_client = mock.create_autospec(docker.Client)

    def test_build_with_build_error(self):
        mock_client = mock.create_autospec(docker.Client)
        service = Service('buildtest', client=mock_client, build='/path')
        with self.assertRaises(BuildError):
            service.build()

    def test_build_with_cache(self):
        mock_client = mock.create_autospec(docker.Client)
        service = Service(
            'buildtest',
            client=mock_client,
            build='/path',
            tags=['foo', 'foo:v2'])
        expected = 'abababab'

        with mock.patch('fig.service.stream_output') as mock_stream_output:
            mock_stream_output.return_value = [
                dict(stream='Successfully built %s' % expected)
            ]
            image_id = service.build()
        self.assertEqual(image_id, expected)
        mock_client.build.assert_called_once_with(
            '/path',
            tag=service.full_name,
            stream=True,
            rm=True,
            nocache=False)

        self.assertEqual(mock_client.tag.mock_calls, [
            mock.call(image_id, 'foo', tag=None),
            mock.call(image_id, 'foo', tag='v2'),
        ])

    def test_bad_tags_from_config(self):
        with self.assertRaises(ConfigError) as exc_context:
            Service('something', tags='my_tag_is_a_string')
        self.assertEqual(str(exc_context.exception),
                         'Service something tags must be a list.')

    def test_name_validations(self):
        self.assertRaises(ConfigError, lambda: Service(name=''))

        self.assertRaises(ConfigError, lambda: Service(name=' '))
        self.assertRaises(ConfigError, lambda: Service(name='/'))
        self.assertRaises(ConfigError, lambda: Service(name='!'))
        self.assertRaises(ConfigError, lambda: Service(name='\xe2'))
        self.assertRaises(ConfigError, lambda: Service(name='_'))
        self.assertRaises(ConfigError, lambda: Service(name='____'))
        self.assertRaises(ConfigError, lambda: Service(name='foo_bar'))
        self.assertRaises(ConfigError, lambda: Service(name='__foo_bar__'))

        Service('a')
        Service('foo')

    def test_project_validation(self):
        self.assertRaises(ConfigError, lambda: Service(name='foo', project='_'))
        Service(name='foo', project='bar')

    def test_config_validation(self):
        self.assertRaises(ConfigError, lambda: Service(name='foo', port=['8000']))
        Service(name='foo', ports=['8000'])

    def test_get_volumes_from_container(self):
        container_id = 'aabbccddee'
        service = Service(
            'test',
            volumes_from=[mock.Mock(id=container_id, spec=Container)])

        self.assertEqual(service._get_volumes_from(), [container_id])

    def test_get_volumes_from_intermediate_container(self):
        container_id = 'aabbccddee'
        service = Service('test')
        container = mock.Mock(id=container_id, spec=Container)

        self.assertEqual(service._get_volumes_from(container), [container_id])

    def test_get_volumes_from_service_container_exists(self):
        container_ids = ['aabbccddee', '12345']
        from_service = mock.create_autospec(Service)
        from_service.containers.return_value = [
            mock.Mock(id=container_id, spec=Container)
            for container_id in container_ids
        ]
        service = Service('test', volumes_from=[from_service])

        self.assertEqual(service._get_volumes_from(), container_ids)

    def test_get_volumes_from_service_no_container(self):
        container_id = 'abababab'
        from_service = mock.create_autospec(Service)
        from_service.containers.return_value = []
        from_service.create_container.return_value = mock.Mock(
            id=container_id,
            spec=Container)
        service = Service('test', volumes_from=[from_service])

        self.assertEqual(service._get_volumes_from(), [container_id])
        from_service.create_container.assert_called_once_with()

    def test_split_port(self):
        internal_port, external_port = split_port("127.0.0.1:1000:2000")
        self.assertEqual(internal_port, "2000")
        self.assertEqual(external_port, ("127.0.0.1", "1000"))

        internal_port, external_port = split_port("127.0.0.1:1000:2000/udp")
        self.assertEqual(internal_port, "2000/udp")
        self.assertEqual(external_port, ("127.0.0.1", "1000"))

        internal_port, external_port = split_port("127.0.0.1::2000")
        self.assertEqual(internal_port, "2000")
        self.assertEqual(external_port, ("127.0.0.1",))

        internal_port, external_port = split_port("1000:2000")
        self.assertEqual(internal_port, "2000")
        self.assertEqual(external_port, "1000")

    def test_split_domainname_none(self):
        service = Service('foo', hostname='name', client=self.mock_client)
        self.mock_client.containers.return_value = []
        opts = service._get_container_create_options({})
        self.assertEqual(opts['hostname'], 'name', 'hostname')
        self.assertFalse('domainname' in opts, 'domainname')

    def test_split_domainname_fqdn(self):
        service = Service('foo',
                hostname='name.domain.tld',
                client=self.mock_client)
        self.mock_client.containers.return_value = []
        opts = service._get_container_create_options({})
        self.assertEqual(opts['hostname'], 'name', 'hostname')
        self.assertEqual(opts['domainname'], 'domain.tld', 'domainname')

    def test_split_domainname_both(self):
        service = Service('foo',
                hostname='name',
                domainname='domain.tld',
                client=self.mock_client)
        self.mock_client.containers.return_value = []
        opts = service._get_container_create_options({})
        self.assertEqual(opts['hostname'], 'name', 'hostname')
        self.assertEqual(opts['domainname'], 'domain.tld', 'domainname')

    def test_split_domainname_weird(self):
        service = Service('foo',
                hostname='name.sub',
                domainname='domain.tld',
                client=self.mock_client)
        self.mock_client.containers.return_value = []
        opts = service._get_container_create_options({})
        self.assertEqual(opts['hostname'], 'name.sub', 'hostname')
        self.assertEqual(opts['domainname'], 'domain.tld', 'domainname')

    def test_get_container_not_found(self):
        mock_client = mock.create_autospec(docker.Client)
        mock_client.containers.return_value = []
        service = Service('foo', client=mock_client)

        self.assertRaises(ValueError, service.get_container)

    @mock.patch('fig.service.Container', autospec=True)
    def test_get_container(self, mock_container_class):
        mock_client = mock.create_autospec(docker.Client)
        container_dict = dict(Name='default_foo_2')
        mock_client.containers.return_value = [container_dict]
        service = Service('foo', client=mock_client)

        container = service.get_container(number=2)
        self.assertEqual(container, mock_container_class.from_ps.return_value)
        mock_container_class.from_ps.assert_called_once_with(
            mock_client, container_dict)
