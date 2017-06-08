import matplotlib.pyplot as plt
import tensorflow as tf
import hypergan as hg
import hyperchamber as hc

from hypergan.gan_component import GANComponent
from hypergan.generators.base_generator import BaseGenerator
from hypergan.samplers.base_sampler import BaseSampler

class CustomGenerator(BaseGenerator):
    def create(self):
        gan = self.gan
        config = self.config
        ops = self.ops
        end_features = config.end_features or 1

        ops.describe('custom_generator')

        net = gan.inputs.x
        net = ops.linear(net, end_features)
        net = ops.lookup('tanh')(net)
        self.sample = net
        return net

class CustomDiscriminator(BaseGenerator):
    def create(self):
        gan = self.gan
        config = self.config
        ops = self.ops
        ops.describe('custom_discriminator')

        end_features = 1

        x = gan.inputs.x
        y = gan.inputs.y
        g = gan.generator.sample

        gnet = tf.concat(axis=1, values=[x,g])
        ynet = tf.concat(axis=1, values=[x,y])

        net = tf.concat(axis=0, values=[ynet, gnet])
        net = ops.linear(net, 128)
        net = tf.nn.tanh(net)
        self.sample = net

        return net

class Custom2DDiscriminator(BaseGenerator):
    def create(self):
        gan = self.gan
        config = self.config
        ops = self.ops
        ops.describe('custom_discriminator')

        end_features = 1

        x = gan.inputs.x
        g = gan.generator.sample

        net = tf.concat(axis=0, values=[x,g])

        net = ops.linear(net, 128)
        net = tf.nn.tanh(net)
        self.sample = net

        return net
class Custom2DSampler(BaseSampler):
    def sample(self, filename):
        gan = self.gan
        generator = gan.generator.sample

        sess = gan.session
        config = gan.config
        x_v, z_v = sess.run([gan.inputs.x, gan.encoder.z])

        sample = sess.run(generator, {gan.inputs.x: x_v, gan.encoder.z: z_v})

        plt.clf()
        plt.figure(figsize=(5,5))
        plt.scatter(*zip(*x_v), c='b')
        plt.scatter(*zip(*sample), c='r')
        plt.xlim([-2, 2])
        plt.ylim([-2, 2])
        plt.ylabel("z")
        plt.savefig(filename)
        return [{'image': filename, 'label': '2d'}]


class Custom2DInputDistribution:
    def __init__(self, args):
        def circle(x):
            spherenet = tf.square(x)
            spherenet = tf.reduce_sum(spherenet, 1)
            lam = tf.sqrt(spherenet)
            return x/tf.reshape(lam,[int(lam.get_shape()[0]), 1])

        def modes(x):
            return tf.round(x*2)/2.0

        if args.distribution == 'circle':
            x = tf.random_normal([args.batch_size, 2])
            x = circle(x)
        elif args.distribution == 'modes':
            x = tf.random_uniform([args.batch_size, 2], -1, 1)
            x = modes(x)
        elif args.distribution == 'sin':
            x = tf.random_uniform((1, args.batch_size), -10.5, 10.5 )
            x = tf.transpose(x)
            r_data = tf.random_normal((args.batch_size,1), mean=0, stddev=0.1)
            xy = tf.sin(0.75*x)*7.0+x*0.5+r_data*1.0
            x = tf.concat([xy,x], 1)/16.0

        elif args.distribution == 'arch':
            offset1 = tf.random_uniform((1, args.batch_size), -10, 10 )
            xa = tf.random_uniform((1, 1), 1, 4 )
            xb = tf.random_uniform((1, 1), 1, 4 )
            x1 = tf.random_uniform((1, args.batch_size), -1, 1 )
            xcos = tf.cos(x1*np.pi + offset1)*xa
            xsin = tf.sin(x1*np.pi + offset1)*xb
            x = tf.transpose(tf.concat([xcos,xsin], 0))/16.0

        self.x = x
        self.xy = tf.zeros_like(self.x)
